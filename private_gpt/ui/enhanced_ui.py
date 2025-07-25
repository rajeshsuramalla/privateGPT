"""Enhanced UI with authentication, role-based access, and model selection."""

import logging
import time
import requests
from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Dict, List
import json

import gradio as gr  # type: ignore
from fastapi import FastAPI
from gradio.themes.utils.colors import slate  # type: ignore

from private_gpt.constants import PROJECT_ROOT_PATH
from private_gpt.ui.images import logo_svg

logger = logging.getLogger(__name__)

THIS_DIRECTORY_RELATIVE = Path(__file__).parent.relative_to(PROJECT_ROOT_PATH)
AVATAR_BOT = THIS_DIRECTORY_RELATIVE / "avatar-bot.ico"

UI_TAB_TITLE = "Enhanced Private GPT"

# API base URL
API_BASE_URL = "http://localhost:8001"


class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"


class ChatMode(str, Enum):
    RAG_MODE = "RAG"
    SEARCH_MODE = "Search"
    BASIC_CHAT_MODE = "Basic"


class EnhancedPrivateGPTUI:
    """Enhanced UI with authentication and role-based features."""
    
    def __init__(self):
        self.current_user = None
        self.current_token = None
        self.available_models = []
        self.selected_model = None
        self.user_documents = []
        
    def authenticate_user(self, username: str, password: str) -> tuple[bool, str, dict]:
        """Authenticate user and return success status, message, and user info."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/v1/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_token = data.get("access_token")
                self.current_user = data.get("user")
                
                # Load available models
                self.load_available_models()
                
                # Load user documents
                self.load_user_documents()
                
                return True, f"Welcome, {self.current_user['username']}!", self.current_user
            else:
                return False, "Invalid credentials", {}
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication failed: {str(e)}", {}
    
    def logout_user(self) -> tuple[bool, str]:
        """Logout current user."""
        self.current_user = None
        self.current_token = None
        self.available_models = []
        self.selected_model = None
        self.user_documents = []
        return True, "Logged out successfully"
    
    def load_available_models(self) -> List[str]:
        """Load available models for current user."""
        if not self.current_token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.current_token}"}
            response = requests.get(f"{API_BASE_URL}/v1/chat/models", headers=headers)
            
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [f"{model['provider']}:{model['name']}" for model in models_data.get("models", [])]
                if self.available_models:
                    self.selected_model = self.available_models[0]
                return self.available_models
            else:
                logger.warning(f"Failed to load models: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return []
    
    def load_user_documents(self) -> List[str]:
        """Load documents owned by current user."""
        if not self.current_token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.current_token}"}
            response = requests.get(f"{API_BASE_URL}/v1/ingest/my-documents", headers=headers)
            
            if response.status_code == 200:
                docs_data = response.json()
                self.user_documents = [doc.get("filename", "Unknown") for doc in docs_data.get("documents", [])]
                return self.user_documents
            else:
                logger.warning(f"Failed to load documents: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    def chat_with_model(self, message: str, history: List[List[str]], model: str, mode: ChatMode) -> Iterable[str]:
        """Chat with selected model using enhanced API."""
        if not self.current_token or not message.strip():
            yield "Please login and enter a message."
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.current_token}",
                "Content-Type": "application/json"
            }
            
            # Build request based on mode
            request_data = {
                "messages": [{"role": "user", "content": message}],
                "model": model,
                "stream": True
            }
            
            # Add context based on mode
            if mode == ChatMode.RAG_MODE:
                request_data["use_context"] = True
            elif mode == ChatMode.SEARCH_MODE:
                request_data["use_context"] = True
                request_data["include_sources"] = True
            
            response = requests.post(
                f"{API_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=request_data,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            # Parse SSE data
                            if line.startswith(b'data: '):
                                data = line[6:].decode('utf-8')
                                if data.strip() == '[DONE]':
                                    break
                                
                                chunk_data = json.loads(data)
                                if "choices" in chunk_data and chunk_data["choices"]:
                                    delta = chunk_data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_response += content
                                        yield full_response
                                        time.sleep(0.02)
                        except json.JSONDecodeError:
                            continue
            else:
                error_msg = f"Chat request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    pass
                yield error_msg
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"Error: {str(e)}"
    
    def upload_documents(self, files: List[str]) -> tuple[str, List[str]]:
        """Upload documents to the enhanced API."""
        if not self.current_token:
            return "Please login first", []
        
        if not files:
            return "No files selected", []
        
        try:
            headers = {"Authorization": f"Bearer {self.current_token}"}
            
            uploaded_files = []
            for file_path in files:
                with open(file_path, 'rb') as f:
                    files_data = {"file": (Path(file_path).name, f, "application/octet-stream")}
                    response = requests.post(
                        f"{API_BASE_URL}/v1/ingest/files",
                        headers=headers,
                        files=files_data
                    )
                    
                    if response.status_code == 200:
                        uploaded_files.append(Path(file_path).name)
                    else:
                        logger.error(f"Failed to upload {file_path}: {response.status_code}")
            
            # Refresh document list
            self.load_user_documents()
            
            if uploaded_files:
                return f"Successfully uploaded: {', '.join(uploaded_files)}", self.user_documents
            else:
                return "No files were uploaded successfully", self.user_documents
                
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return f"Upload failed: {str(e)}", []
    
    def create_login_interface(self) -> gr.Blocks:
        """Create the login interface."""
        with gr.Blocks(
            title=UI_TAB_TITLE,
            theme=gr.themes.Soft(primary_hue=slate),
            css="""
            .login-container { 
                max-width: 400px; 
                margin: 0 auto; 
                padding: 2rem; 
                border-radius: 10px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }
            .login-title { 
                text-align: center; 
                color: white; 
                font-size: 2rem; 
                margin-bottom: 1rem; 
                font-weight: bold;
            }
            .login-subtitle { 
                text-align: center; 
                color: rgba(255,255,255,0.8); 
                margin-bottom: 2rem; 
            }
            .demo-users {
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
                color: white;
            }
            """
        ) as login_blocks:
            
            with gr.Column(elem_classes="login-container"):
                gr.HTML('<div class="login-title">🔐 Enhanced PrivateGPT</div>')
                gr.HTML('<div class="login-subtitle">Role-based access with multi-model support</div>')
                
                # Demo users info
                with gr.Group():
                    gr.HTML("""
                    <div class="demo-users">
                        <h4>🎯 Demo Users Available:</h4>
                        <p><strong>SuperAdmin:</strong> username: <code>superadmin</code>, password: <code>admin123!</code></p>
                        <p><strong>Admin:</strong> username: <code>admin</code>, password: <code>admin123!</code></p>
                        <p><strong>User:</strong> username: <code>user</code>, password: <code>user123!</code></p>
                    </div>
                    """)
                
                username_input = gr.Textbox(
                    label="Username",
                    placeholder="Enter your username",
                    scale=1
                )
                
                password_input = gr.Textbox(
                    label="Password",
                    placeholder="Enter your password",
                    type="password",
                    scale=1
                )
                
                login_button = gr.Button("🚀 Login", variant="primary", size="lg")
                
                login_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    visible=False
                )
                
                # Hidden component to store user info
                user_info = gr.JSON(visible=False)
                
                def handle_login(username: str, password: str):
                    success, message, user_data = self.authenticate_user(username, password)
                    if success:
                        return {
                            login_status: gr.update(value=message, visible=True),
                            user_info: user_data,
                            "__type__": "update"
                        }
                    else:
                        return {
                            login_status: gr.update(value=message, visible=True),
                            user_info: {},
                            "__type__": "update"
                        }
                
                login_button.click(
                    handle_login,
                    inputs=[username_input, password_input],
                    outputs=[login_status, user_info]
                )
                
        return login_blocks
    
    def create_main_interface(self) -> gr.Blocks:
        """Create the main interface after authentication."""
        with gr.Blocks(
            title=UI_TAB_TITLE,
            theme=gr.themes.Soft(primary_hue=slate),
            css="""
            .header-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                color: white;
            }
            .user-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .model-selector {
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
            }
            """
        ) as main_blocks:
            
            # Header with user info and logout
            with gr.Row():
                with gr.Column(scale=4):
                    user_display = gr.HTML()
                with gr.Column(scale=1):
                    logout_button = gr.Button("🚪 Logout", size="sm")
            
            with gr.Row():
                # Left sidebar - Model selection and documents
                with gr.Column(scale=1):
                    # Model selection
                    gr.HTML("<h3>🤖 Available Models</h3>")
                    model_dropdown = gr.Dropdown(
                        choices=self.available_models,
                        value=self.selected_model,
                        label="Select Model",
                        interactive=True
                    )
                    
                    # Chat mode selection
                    gr.HTML("<h3>💬 Chat Mode</h3>")
                    mode_radio = gr.Radio(
                        choices=[mode.value for mode in ChatMode],
                        value=ChatMode.RAG_MODE.value,
                        label="Mode"
                    )
                    
                    # Document management
                    gr.HTML("<h3>📄 Document Management</h3>")
                    upload_files = gr.File(
                        label="Upload Documents",
                        file_count="multiple",
                        file_types=[".txt", ".pdf", ".docx", ".md"]
                    )
                    
                    upload_status = gr.Textbox(
                        label="Upload Status",
                        interactive=False,
                        visible=False
                    )
                    
                    user_docs_list = gr.List(
                        value=self.user_documents,
                        label="My Documents",
                        headers=["Document Name"]
                    )
                
                # Main chat area
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        label="Enhanced PrivateGPT Chat",
                        height=500,
                        avatar_images=[None, AVATAR_BOT]
                    )
                    
                    with gr.Row():
                        with gr.Column(scale=4):
                            msg_input = gr.Textbox(
                                label="Message",
                                placeholder="Ask anything about your documents...",
                                lines=2
                            )
                        with gr.Column(scale=1, min_width=100):
                            send_button = gr.Button("📤 Send", variant="primary")
                            clear_button = gr.Button("🧹 Clear", variant="secondary")
            
            # Event handlers
            def update_user_display():
                if self.current_user:
                    role_emoji = {"superadmin": "👑", "admin": "🛡️", "user": "👤"}
                    emoji = role_emoji.get(self.current_user.get("role", "user"), "👤")
                    return f"""
                    <div class="header-container">
                        <div class="user-info">
                            <div>
                                <h2>{emoji} Welcome, {self.current_user['username']}!</h2>
                                <p>Role: {self.current_user['role'].title()} | Models Available: {len(self.available_models)}</p>
                            </div>
                        </div>
                    </div>
                    """
                return ""
            
            def handle_chat(message: str, history: List[List[str]], model: str, mode: str):
                if not message.strip():
                    return history, ""
                
                # Add user message to history
                history.append([message, ""])
                
                # Get response from API
                response_gen = self.chat_with_model(message, history, model, ChatMode(mode))
                
                # Stream the response
                for response in response_gen:
                    history[-1][1] = response
                    yield history, ""
            
            def handle_upload(files):
                if files:
                    file_paths = [file.name for file in files]
                    status, docs = self.upload_documents(file_paths)
                    return {
                        upload_status: gr.update(value=status, visible=True),
                        user_docs_list: docs
                    }
                return {
                    upload_status: gr.update(value="No files selected", visible=True),
                    user_docs_list: self.user_documents
                }
            
            def handle_logout():
                success, message = self.logout_user()
                return message
            
            # Wire up events
            main_blocks.load(
                update_user_display,
                outputs=user_display
            )
            
            send_button.click(
                handle_chat,
                inputs=[msg_input, chatbot, model_dropdown, mode_radio],
                outputs=[chatbot, msg_input]
            )
            
            msg_input.submit(
                handle_chat,
                inputs=[msg_input, chatbot, model_dropdown, mode_radio],
                outputs=[chatbot, msg_input]
            )
            
            clear_button.click(
                lambda: ([], ""),
                outputs=[chatbot, msg_input]
            )
            
            upload_files.upload(
                handle_upload,
                inputs=upload_files,
                outputs=[upload_status, user_docs_list]
            )
            
            logout_button.click(
                handle_logout,
                outputs=login_status  # This would need to be handled by parent
            )
        
        return main_blocks
    
    def create_enhanced_ui(self) -> gr.Blocks:
        """Create the complete enhanced UI with authentication flow."""
        with gr.Blocks(
            title=UI_TAB_TITLE,
            theme=gr.themes.Soft(primary_hue=slate)
        ) as enhanced_ui:
            
            # State management
            authenticated = gr.State(False)
            
            # Create both interfaces
            login_interface = self.create_login_interface()
            main_interface = self.create_main_interface()
            
            # Initially show login interface
            login_interface.render()
            
            with gr.Column(visible=False) as main_container:
                main_interface.render()
            
            # Handle authentication flow
            def handle_auth_change(is_auth: bool):
                return {
                    login_interface: gr.update(visible=not is_auth),
                    main_container: gr.update(visible=is_auth)
                }
            
            authenticated.change(
                handle_auth_change,
                inputs=authenticated,
                outputs=[login_interface, main_container]
            )
        
        return enhanced_ui


def create_enhanced_ui_app() -> gr.Blocks:
    """Create and return the enhanced UI application."""
    ui = EnhancedPrivateGPTUI()
    return ui.create_enhanced_ui()


# For backward compatibility
def create_ui_blocks() -> gr.Blocks:
    """Create UI blocks for integration with existing launcher."""
    return create_enhanced_ui_app()
