"""
Automated CSV Preprocessing Module for PrivateGPT
Automatically detects and processes CSV files during ingestion.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import specialized energy data processor
from .energy_data_processor import EnergyDataProcessor

logger = logging.getLogger(__name__)

class AutoCSVProcessor:
    """Automatically processes CSV files into intelligent narratives for PrivateGPT."""
    
    def __init__(self):
        self.supported_extensions = ['.csv', '.CSV']
        self.energy_processor = EnergyDataProcessor()
        
    def is_csv_file(self, file_path: Path) -> bool:
        """Check if file is a CSV file."""
        return file_path.suffix in self.supported_extensions
    
    def detect_csv_type(self, df: pd.DataFrame) -> str:
        """Detect what type of CSV data this is."""
        columns = [col.lower() for col in df.columns]
        
        # Check for time-series/sensor data
        time_indicators = ['time', 'timestamp', 'date', 'sample', 'reading']
        value_indicators = ['value', 'reading', 'measurement', 'data', 'signal']
        device_indicators = ['device', 'sensor', 'equipment', 'id', 'sid']
        
        has_time = any(indicator in ' '.join(columns) for indicator in time_indicators)
        has_values = any(indicator in ' '.join(columns) for indicator in value_indicators)
        has_devices = any(indicator in ' '.join(columns) for indicator in device_indicators)
        
        if has_time and has_values and has_devices:
            return "sensor_data"
        elif has_time and has_values:
            return "time_series"
        elif len(df.columns) > 5 and df.shape[0] > 1000:
            return "large_dataset"
        else:
            return "general_data"
    
    def process_sensor_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process sensor/industrial data like our previous example."""
        # Identify key columns
        value_cols = []
        time_cols = []
        device_cols = []
        
        for col in df.columns:
            col_lower = col.lower()
            if 'value' in col_lower or 'reading' in col_lower or 'measurement' in col_lower:
                value_cols.append(col)
            elif 'time' in col_lower or 'date' in col_lower:
                time_cols.append(col)
            elif 'device' in col_lower or 'sensor' in col_lower or 'id' in col_lower:
                device_cols.append(col)
        
        # Use first available columns if specific ones not found
        if not value_cols:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            value_cols = [numeric_cols[0]] if len(numeric_cols) > 0 else []
        
        if not value_cols:
            return self.process_general_data(df, filename)
        
        value_col = value_cols[0]
        device_col = device_cols[0] if device_cols else None
        time_col = time_cols[0] if time_cols else None
        
        # Convert to numeric
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        df = df.dropna(subset=[value_col])
        
        if len(df) == 0:
            return f"ERROR: No valid numeric data found in {filename}"
        
        # Group by device if available
        if device_col and df[device_col].nunique() > 1:
            return self.process_multi_device_data(df, value_col, device_col, time_col, filename)
        else:
            return self.process_single_device_data(df, value_col, time_col, filename)
    
    def process_single_device_data(self, df: pd.DataFrame, value_col: str, time_col: str, filename: str) -> str:
        """Process single device sensor data."""
        values = df[value_col]
        
        # Basic statistics
        stats = {
            'count': len(values),
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
            'range': values.max() - values.min()
        }
        
        # Trend analysis
        if len(values) >= 100:
            recent_data = values.tail(min(1000, len(values)//4))
            trend_slope = np.polyfit(range(len(recent_data)), recent_data, 1)[0]
        else:
            trend_slope = 0
        
        # Risk assessment
        cv = stats['std'] / stats['mean'] if stats['mean'] != 0 else 0
        
        if cv > 0.5:
            risk_level = "HIGH"
            risk_reason = f"High variability (CV: {cv:.1%})"
        elif abs(trend_slope) > stats['std'] * 0.1:
            risk_level = "MEDIUM"
            risk_reason = f"Significant trend detected (slope: {trend_slope:.4f})"
        else:
            risk_level = "LOW"
            risk_reason = "Stable operation"
        
        # Time analysis
        time_info = ""
        if time_col and time_col in df.columns:
            try:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                time_range = df[time_col].max() - df[time_col].min()
                time_info = f"\nTemporal Analysis:\n• Data Period: {time_range}\n• Sampling Rate: {len(df)/time_range.total_seconds()*3600:.1f} readings/hour"
            except:
                time_info = "\n• Time analysis: Unable to parse time data"
        
        return f"""AUTOMATED CSV ANALYSIS REPORT
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Single Device Sensor Data

========================================
📊 DATASET OVERVIEW
========================================

Data Characteristics:
• Total Measurements: {stats['count']:,}
• Value Column: {value_col}
• Operational Range: {stats['min']:.3f} to {stats['max']:.3f}
• Average Value: {stats['mean']:.3f} ± {stats['std']:.3f}
• Coefficient of Variation: {cv:.1%}{time_info}

========================================
🎯 OPERATIONAL ASSESSMENT
========================================

Performance Metrics:
• Risk Level: {risk_level}
• Assessment: {risk_reason}
• Data Quality: {'Excellent' if cv < 0.1 else 'Good' if cv < 0.3 else 'Poor'}
• Trend Direction: {'Increasing' if trend_slope > 0.01 else 'Decreasing' if trend_slope < -0.01 else 'Stable'}

Control Limits (±3σ):
• Upper Limit: {stats['mean'] + 3*stats['std']:.3f}
• Center Line: {stats['mean']:.3f}
• Lower Limit: {stats['mean'] - 3*stats['std']:.3f}

========================================
🔧 RECOMMENDATIONS
========================================

Immediate Actions:
{'• URGENT: Investigate high process variability' if risk_level == 'HIGH' else '• Monitor for trend changes' if risk_level == 'MEDIUM' else '• Continue standard operations'}

Monitoring:
• Track values outside control limits
• Watch for trend changes > {stats['std']*0.1:.3f} per reading
• Review data quality if variability increases

Maintenance:
{'• Schedule equipment inspection due to instability' if risk_level == 'HIGH' else '• Plan preventive maintenance based on trends' if risk_level == 'MEDIUM' else '• Continue routine maintenance schedule'}

========================================
SUMMARY: {risk_level} risk level detected. {risk_reason}.
========================================
"""
    
    def process_multi_device_data(self, df: pd.DataFrame, value_col: str, device_col: str, time_col: str, filename: str) -> str:
        """Process multi-device sensor data."""
        devices = df[device_col].unique()
        device_summaries = []
        
        for device in devices:
            if pd.isna(device):
                continue
                
            device_data = df[df[device_col] == device][value_col]
            if len(device_data) == 0:
                continue
            
            stats = {
                'count': len(device_data),
                'mean': device_data.mean(),
                'std': device_data.std(),
                'min': device_data.min(),
                'max': device_data.max()
            }
            
            cv = stats['std'] / stats['mean'] if stats['mean'] != 0 else 0
            risk = "HIGH" if cv > 0.5 else "MEDIUM" if cv > 0.3 else "LOW"
            
            device_summaries.append(f"""
Device {device}:
• Readings: {stats['count']:,}
• Average: {stats['mean']:.2f} ± {stats['std']:.2f}
• Range: {stats['min']:.2f} to {stats['max']:.2f}
• Risk Level: {risk}
• Status: {'⚠️ Needs attention' if risk in ['HIGH', 'MEDIUM'] else '✅ Normal operation'}""")
        
        high_risk_devices = len([d for d in device_summaries if 'HIGH' in d])
        medium_risk_devices = len([d for d in device_summaries if 'MEDIUM' in d])
        
        return f"""AUTOMATED MULTI-DEVICE CSV ANALYSIS
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Multi-Device Sensor Network

========================================
🏭 FLEET OVERVIEW
========================================

Network Summary:
• Total Devices: {len(devices)}
• High Risk Devices: {high_risk_devices}
• Medium Risk Devices: {medium_risk_devices}
• Normal Devices: {len(devices) - high_risk_devices - medium_risk_devices}
• Total Data Points: {len(df):,}

========================================
📊 DEVICE-BY-DEVICE ANALYSIS
========================================
{''.join(device_summaries)}

========================================
🚨 FLEET MANAGEMENT PRIORITIES
========================================

Immediate Attention Required:
{f'• {high_risk_devices} devices need urgent inspection' if high_risk_devices > 0 else '• No high-risk devices identified'}

Monitoring Required:
{f'• {medium_risk_devices} devices require increased monitoring' if medium_risk_devices > 0 else '• All devices operating normally'}

Recommended Actions:
1. Prioritize maintenance for high-risk devices
2. Implement automated monitoring for the fleet
3. Establish baseline performance metrics
4. Schedule regular equipment health assessments

========================================
EXECUTIVE SUMMARY: {high_risk_devices + medium_risk_devices} of {len(devices)} devices require attention.
========================================
"""
    
    def process_time_series(self, df: pd.DataFrame, filename: str) -> str:
        """Process general time-series data."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            return self.process_general_data(df, filename)
        
        summary = f"""AUTOMATED TIME-SERIES ANALYSIS
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Time-Series Dataset

========================================
📈 TIME-SERIES OVERVIEW
========================================

Dataset Characteristics:
• Total Records: {len(df):,}
• Numeric Variables: {len(numeric_columns)}
• Time Span: {len(df)} data points

Variable Analysis:
"""
        
        for col in numeric_columns[:5]:  # Limit to first 5 numeric columns
            values = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(values) > 0:
                trend = np.polyfit(range(len(values)), values, 1)[0] if len(values) > 1 else 0
                summary += f"""
{col}:
• Range: {values.min():.2f} to {values.max():.2f}
• Average: {values.mean():.2f} ± {values.std():.2f}
• Trend: {'Increasing' if trend > 0 else 'Decreasing' if trend < 0 else 'Stable'}
• Data Quality: {len(values)/len(df)*100:.1f}% complete"""
        
        summary += f"""

========================================
🎯 KEY INSIGHTS
========================================

Data Completeness: {df.isnull().sum().sum()/(len(df)*len(df.columns))*100:.1f}% missing values
Primary Variables: {', '.join(numeric_columns[:3])}
Recommended Focus: Monitor trends in key variables for anomaly detection

========================================
"""
        return summary
    
    def process_large_dataset(self, df: pd.DataFrame, filename: str) -> str:
        """Process large general datasets."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        return f"""AUTOMATED LARGE DATASET ANALYSIS
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Large Structured Dataset

========================================
📊 DATASET STRUCTURE
========================================

Data Dimensions:
• Total Records: {len(df):,}
• Total Columns: {len(df.columns)}
• Numeric Columns: {len(numeric_cols)}
• Categorical Columns: {len(categorical_cols)}
• Memory Usage: ~{df.memory_usage(deep=True).sum()/1024/1024:.1f} MB

Data Quality:
• Missing Values: {df.isnull().sum().sum():,} ({df.isnull().sum().sum()/(len(df)*len(df.columns))*100:.1f}%)
• Duplicate Records: {df.duplicated().sum():,}
• Unique Records: {len(df) - df.duplicated().sum():,}

========================================
📈 KEY VARIABLES ANALYSIS
========================================

Numeric Variables Summary:
{df[numeric_cols].describe().round(2).to_string() if len(numeric_cols) > 0 else 'No numeric variables found'}

Categorical Variables:
{chr(10).join([f'• {col}: {df[col].nunique()} unique values' for col in categorical_cols[:5]]) if len(categorical_cols) > 0 else 'No categorical variables found'}

========================================
🎯 ANALYSIS RECOMMENDATIONS
========================================

Data Exploration:
• Focus on top numeric variables for trend analysis
• Investigate categorical distributions for patterns
• Consider correlation analysis between key variables

Quality Improvements:
• Address missing values in key columns
• Validate data types and ranges
• Check for outliers in numeric variables

Business Intelligence:
• Suitable for dashboards and reporting
• Good candidate for statistical modeling
• Consider time-based analysis if temporal data exists

========================================
"""
    
    def process_general_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process general CSV data."""
        return f"""AUTOMATED CSV DATA ANALYSIS
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: General Structured Data

========================================
📋 DATA SUMMARY
========================================

Basic Information:
• Records: {len(df):,}
• Columns: {len(df.columns)}
• Column Names: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}

Data Sample (First 5 Rows):
{df.head().to_string()}

Data Types:
{df.dtypes.to_string()}

========================================
🔍 QUICK INSIGHTS
========================================

• Data structure appears suitable for analysis
• Contains {len(df.select_dtypes(include=[np.number]).columns)} numeric and {len(df.select_dtypes(include=['object']).columns)} text columns
• Recommended for further data exploration and visualization

========================================
"""
    
    def process_csv_file(self, file_path: Path) -> str:
        """Main processing function - converts CSV to intelligent narrative."""
        try:
            logger.info(f"Auto-processing CSV file: {file_path}")
            
            # Load CSV
            df = pd.read_csv(file_path, low_memory=False)
            
            if len(df) == 0:
                return f"ERROR: Empty CSV file - {file_path}"
            
            # First, try specialized energy data processing
            energy_data_type = self.energy_processor.detect_energy_data_type(df)
            
            if energy_data_type != "unknown_energy_type":
                logger.info(f"Detected specialized energy data type: {energy_data_type}")
                return self.energy_processor.process_csv_file(file_path)
            
            # Fall back to general CSV type detection and processing
            csv_type = self.detect_csv_type(df)
            logger.info(f"Detected general CSV type: {csv_type}")
            
            if csv_type == "sensor_data":
                return self.process_sensor_data(df, file_path.name)
            elif csv_type == "time_series":
                return self.process_time_series(df, file_path.name)
            elif csv_type == "large_dataset":
                return self.process_large_dataset(df, file_path.name)
            else:
                return self.process_general_data(df, file_path.name)
                
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            return f"ERROR: Failed to process CSV file {file_path}: {str(e)}"

# Global instance for use by PrivateGPT
csv_processor = AutoCSVProcessor()
