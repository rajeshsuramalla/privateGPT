"""
Energy Data Preprocessors for PrivateGPT
Specialized processors for different types of energy and building systems data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class EnergyDataProcessor:
    """Specialized processor for various energy and building systems data types."""
    
    def __init__(self):
        self.supported_extensions = ['.csv', '.CSV']
        
    def detect_energy_data_type(self, df: pd.DataFrame) -> str:
        """Detect specific type of energy data."""
        columns = [col.lower() for col in df.columns]
        column_text = ' '.join(columns)
        
        # Energy consumption data indicators
        if any(indicator in column_text for indicator in ['kwh', 'power', 'consumption', 'usage', 'demand']):
            if any(indicator in column_text for indicator in ['meter', 'reading', 'cumulative']):
                return "energy_meter"
            elif any(indicator in column_text for indicator in ['hvac', 'cooling', 'heating', 'chiller', 'boiler']):
                return "hvac_energy"
            elif any(indicator in column_text for indicator in ['lighting', 'plug', 'equipment']):
                return "equipment_energy"
            else:
                return "general_energy"
                
        # Electrical parameters
        elif any(indicator in column_text for indicator in ['voltage', 'current', 'frequency', 'pf', 'power_factor']):
            return "electrical_parameters"
            
        # Building automation/BMS data
        elif any(indicator in column_text for indicator in ['setpoint', 'temperature', 'humidity', 'pressure']):
            if any(indicator in column_text for indicator in ['zone', 'room', 'space', 'ahu', 'vav']):
                return "building_automation"
            else:
                return "environmental_sensors"
                
        # Alarm and event data
        elif any(indicator in column_text for indicator in ['alarm', 'alert', 'fault', 'error', 'warning']):
            return "alarm_data"
            
        # Trend/historical data
        elif any(indicator in column_text for indicator in ['trend', 'history', 'log']):
            return "trend_data"
            
        else:
            return "unknown_energy_type"
    
    def process_energy_meter_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process energy meter readings (kWh, demand, etc.)."""
        # Identify key columns
        energy_cols = []
        demand_cols = []
        time_cols = []
        meter_cols = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(indicator in col_lower for indicator in ['kwh', 'energy', 'consumption', 'usage']):
                energy_cols.append(col)
            elif any(indicator in col_lower for indicator in ['kw', 'demand', 'power']):
                demand_cols.append(col)
            elif any(indicator in col_lower for indicator in ['time', 'date', 'timestamp']):
                time_cols.append(col)
            elif any(indicator in col_lower for indicator in ['meter', 'id', 'device', 'point']):
                meter_cols.append(col)
        
        if not energy_cols and not demand_cols:
            return "ERROR: No energy consumption or demand data found"
        
        # Analyze energy consumption
        analysis_results = []
        
        # Process energy consumption
        if energy_cols:
            energy_col = energy_cols[0]
            df[energy_col] = pd.to_numeric(df[energy_col], errors='coerce')
            df = df.dropna(subset=[energy_col])
            
            total_consumption = df[energy_col].sum()
            avg_consumption = df[energy_col].mean()
            peak_consumption = df[energy_col].max()
            
            # Calculate daily patterns if time data available
            daily_pattern = ""
            if time_cols:
                try:
                    time_col = time_cols[0]
                    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                    df['hour'] = df[time_col].dt.hour
                    hourly_avg = df.groupby('hour')[energy_col].mean()
                    peak_hour = hourly_avg.idxmax()
                    daily_pattern = f"\n• Peak Usage Hour: {peak_hour}:00"
                except:
                    daily_pattern = "\n• Daily pattern analysis unavailable"
            
            analysis_results.append(f"""
📊 ENERGY CONSUMPTION ANALYSIS:
• Total Consumption: {total_consumption:,.1f} kWh
• Average Reading: {avg_consumption:.1f} kWh
• Peak Reading: {peak_consumption:.1f} kWh{daily_pattern}""")
        
        # Process demand data
        if demand_cols:
            demand_col = demand_cols[0]
            df[demand_col] = pd.to_numeric(df[demand_col], errors='coerce')
            
            max_demand = df[demand_col].max()
            avg_demand = df[demand_col].mean()
            load_factor = avg_demand / max_demand if max_demand > 0 else 0
            
            analysis_results.append(f"""
⚡ DEMAND ANALYSIS:
• Maximum Demand: {max_demand:.1f} kW
• Average Demand: {avg_demand:.1f} kW
• Load Factor: {load_factor:.1%}
• Demand Efficiency: {'Excellent' if load_factor > 0.7 else 'Good' if load_factor > 0.5 else 'Poor'}""")
        
        # Cost analysis (assuming $0.12/kWh average)
        if energy_cols:
            estimated_cost = total_consumption * 0.12
            analysis_results.append(f"""
💰 COST ANALYSIS:
• Estimated Energy Cost: ${estimated_cost:,.2f}
• Cost per Reading: ${estimated_cost/len(df):,.2f}""")
        
        return f"""ENERGY METER DATA ANALYSIS REPORT
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Energy Meter Readings

========================================
🏢 METER OVERVIEW
========================================

Dataset Characteristics:
• Total Readings: {len(df):,}
• Data Period: {df[time_cols[0]].min()} to {df[time_cols[0]].max() if time_cols else 'Unknown'}
• Meter Points: {df[meter_cols[0]].nunique() if meter_cols else 1}

========================================
📈 ENERGY PERFORMANCE METRICS
========================================
{''.join(analysis_results)}

========================================
🎯 ENERGY MANAGEMENT INSIGHTS
========================================

Performance Assessment:
• Load Pattern: {'Consistent' if energy_cols and df[energy_cols[0]].std()/df[energy_cols[0]].mean() < 0.3 else 'Variable'}
• Energy Efficiency: Based on load factor and consumption patterns
• Optimization Potential: {'High' if load_factor < 0.5 else 'Medium' if load_factor < 0.7 else 'Low'}

Recommendations:
• Monitor peak demand periods for cost optimization
• Analyze consumption patterns for energy efficiency opportunities
• Consider load shifting strategies during high-demand periods
• Implement demand response programs if applicable

========================================
📊 DATA QUALITY ASSESSMENT
========================================

Data Completeness: {(1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100:.1f}%
Missing Values: {df.isnull().sum().sum()} out of {len(df) * len(df.columns)} total data points
Data Range: {len(df)} readings across {(df[time_cols[0]].max() - df[time_cols[0]].min()).days if time_cols else 'Unknown'} days

This analysis provides insights into energy consumption patterns, demand characteristics, 
and cost implications for strategic energy management decisions."""
    
    def process_hvac_energy_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process HVAC energy consumption data."""
        # Identify HVAC-specific columns
        cooling_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['cooling', 'chiller', 'ac', 'refrigeration'])]
        heating_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['heating', 'boiler', 'heat'])]
        fan_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['fan', 'ahu', 'ventilation'])]
        temp_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['temp', 'temperature'])]
        
        results = []
        
        # Analyze cooling energy
        if cooling_cols:
            cooling_col = cooling_cols[0]
            df[cooling_col] = pd.to_numeric(df[cooling_col], errors='coerce')
            cooling_total = df[cooling_col].sum()
            cooling_avg = df[cooling_col].mean()
            results.append(f"""
❄️ COOLING SYSTEM ANALYSIS:
• Total Cooling Energy: {cooling_total:,.1f} kWh
• Average Cooling Load: {cooling_avg:.1f} kWh
• Peak Cooling Demand: {df[cooling_col].max():.1f} kWh""")
        
        # Analyze heating energy
        if heating_cols:
            heating_col = heating_cols[0]
            df[heating_col] = pd.to_numeric(df[heating_col], errors='coerce')
            heating_total = df[heating_col].sum()
            heating_avg = df[heating_col].mean()
            results.append(f"""
🔥 HEATING SYSTEM ANALYSIS:
• Total Heating Energy: {heating_total:,.1f} kWh
• Average Heating Load: {heating_avg:.1f} kWh
• Peak Heating Demand: {df[heating_col].max():.1f} kWh""")
        
        # Calculate efficiency metrics
        if cooling_cols and heating_cols:
            total_hvac = df[cooling_cols[0]].sum() + df[heating_cols[0]].sum()
            cooling_ratio = df[cooling_cols[0]].sum() / total_hvac
            results.append(f"""
⚖️ HVAC BALANCE ANALYSIS:
• Total HVAC Energy: {total_hvac:,.1f} kWh
• Cooling vs Heating Ratio: {cooling_ratio:.1%} cooling, {1-cooling_ratio:.1%} heating
• System Balance: {'Cooling Dominant' if cooling_ratio > 0.6 else 'Heating Dominant' if cooling_ratio < 0.4 else 'Balanced'}""")
        
        return f"""HVAC ENERGY ANALYSIS REPORT
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: HVAC Energy Consumption

========================================
🏗️ HVAC SYSTEM OVERVIEW
========================================

System Components Detected:
• Cooling Systems: {len(cooling_cols)} data streams
• Heating Systems: {len(heating_cols)} data streams  
• Ventilation/Fans: {len(fan_cols)} data streams
• Temperature Sensors: {len(temp_cols)} monitoring points

========================================
📊 ENERGY CONSUMPTION BREAKDOWN
========================================
{''.join(results)}

========================================
🎯 HVAC OPTIMIZATION INSIGHTS
========================================

Energy Efficiency Opportunities:
• Implement advanced controls for load optimization
• Consider variable speed drives for fans and pumps
• Optimize setpoints based on occupancy patterns
• Evaluate economizer operations during suitable weather

Maintenance Priorities:
• Monitor filter conditions affecting fan energy
• Check refrigerant levels for cooling efficiency
• Verify heating system combustion efficiency
• Calibrate temperature sensors for accurate control

This analysis helps identify HVAC energy patterns and optimization opportunities
for improved building energy performance and occupant comfort."""
    
    def process_electrical_parameters_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process electrical parameters (voltage, current, power factor, etc.)."""
        voltage_cols = [col for col in df.columns if 'voltage' in col.lower() or 'volt' in col.lower()]
        current_cols = [col for col in df.columns if 'current' in col.lower() or 'amp' in col.lower()]
        pf_cols = [col for col in df.columns if 'power' in col.lower() and 'factor' in col.lower() or 'pf' in col.lower()]
        freq_cols = [col for col in df.columns if 'frequency' in col.lower() or 'freq' in col.lower()]
        
        results = []
        
        # Analyze voltage
        if voltage_cols:
            voltage_col = voltage_cols[0]
            df[voltage_col] = pd.to_numeric(df[voltage_col], errors='coerce')
            v_avg = df[voltage_col].mean()
            v_std = df[voltage_col].std()
            v_variation = (v_std / v_avg) * 100
            
            # Voltage quality assessment
            voltage_quality = "Excellent" if v_variation < 2 else "Good" if v_variation < 5 else "Poor"
            
            results.append(f"""
⚡ VOLTAGE ANALYSIS:
• Average Voltage: {v_avg:.1f} V
• Voltage Variation: ±{v_std:.1f} V ({v_variation:.1f}%)
• Voltage Quality: {voltage_quality}
• Min/Max: {df[voltage_col].min():.1f}V to {df[voltage_col].max():.1f}V""")
        
        # Analyze current
        if current_cols:
            current_col = current_cols[0]
            df[current_col] = pd.to_numeric(df[current_col], errors='coerce')
            i_avg = df[current_col].mean()
            i_max = df[current_col].max()
            
            results.append(f"""
🔌 CURRENT ANALYSIS:
• Average Current: {i_avg:.1f} A
• Peak Current: {i_max:.1f} A
• Load Factor: {i_avg/i_max:.1%}""")
        
        # Analyze power factor
        if pf_cols:
            pf_col = pf_cols[0]
            df[pf_col] = pd.to_numeric(df[pf_col], errors='coerce')
            pf_avg = df[pf_col].mean()
            pf_min = df[pf_col].min()
            
            pf_quality = "Excellent" if pf_avg > 0.95 else "Good" if pf_avg > 0.85 else "Poor"
            
            results.append(f"""
📈 POWER FACTOR ANALYSIS:
• Average Power Factor: {pf_avg:.3f}
• Minimum Power Factor: {pf_min:.3f}
• Power Quality: {pf_quality}
• Reactive Power Impact: {'Minimal' if pf_avg > 0.95 else 'Moderate' if pf_avg > 0.85 else 'Significant'}""")
        
        return f"""ELECTRICAL PARAMETERS ANALYSIS REPORT
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Electrical System Parameters

========================================
⚡ ELECTRICAL SYSTEM OVERVIEW
========================================

Parameters Monitored:
• Voltage Measurements: {len(voltage_cols)} channels
• Current Measurements: {len(current_cols)} channels
• Power Factor Data: {len(pf_cols)} measurements
• Frequency Data: {len(freq_cols)} measurements

========================================
📊 ELECTRICAL QUALITY ANALYSIS
========================================
{''.join(results)}

========================================
🎯 POWER QUALITY ASSESSMENT
========================================

System Health:
• Voltage Stability: Based on variation analysis
• Load Balance: Analyzed from current patterns
• Reactive Power Management: Power factor performance
• Harmonic Distortion: Frequency analysis where available

Recommendations:
• Monitor voltage variations for equipment protection
• Implement power factor correction if needed
• Consider harmonic filtering for sensitive equipment
• Regular calibration of monitoring equipment

This analysis provides insights into electrical system performance
and power quality for reliable facility operations."""
    
    def process_building_automation_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process building automation system (BAS/BMS) data."""
        temp_cols = [col for col in df.columns if 'temp' in col.lower()]
        humidity_cols = [col for col in df.columns if 'humidity' in col.lower() or 'rh' in col.lower()]
        pressure_cols = [col for col in df.columns if 'pressure' in col.lower()]
        setpoint_cols = [col for col in df.columns if 'setpoint' in col.lower() or 'sp' in col.lower()]
        zone_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['zone', 'room', 'space'])]
        
        results = []
        
        # Temperature analysis
        if temp_cols:
            temp_col = temp_cols[0]
            df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
            temp_avg = df[temp_col].mean()
            temp_range = df[temp_col].max() - df[temp_col].min()
            
            comfort_assessment = "Optimal" if 68 <= temp_avg <= 76 else "Acceptable" if 65 <= temp_avg <= 80 else "Poor"
            
            results.append(f"""
🌡️ TEMPERATURE CONTROL:
• Average Temperature: {temp_avg:.1f}°F
• Temperature Range: {temp_range:.1f}°F
• Comfort Assessment: {comfort_assessment}
• Stability: {'Stable' if temp_range < 5 else 'Variable'}""")
        
        # Humidity analysis
        if humidity_cols:
            humidity_col = humidity_cols[0]
            df[humidity_col] = pd.to_numeric(df[humidity_col], errors='coerce')
            humidity_avg = df[humidity_col].mean()
            
            humidity_assessment = "Optimal" if 30 <= humidity_avg <= 50 else "Acceptable" if 25 <= humidity_avg <= 60 else "Poor"
            
            results.append(f"""
💧 HUMIDITY CONTROL:
• Average Humidity: {humidity_avg:.1f}% RH
• Humidity Assessment: {humidity_assessment}
• IAQ Impact: {'Excellent' if 30 <= humidity_avg <= 50 else 'Acceptable' if 25 <= humidity_avg <= 60 else 'Needs Attention'}""")
        
        return f"""BUILDING AUTOMATION SYSTEM ANALYSIS
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Building Automation/Environmental Control

========================================
🏢 BUILDING CONTROL OVERVIEW
========================================

Control Points Monitored:
• Temperature Sensors: {len(temp_cols)} points
• Humidity Sensors: {len(humidity_cols)} points
• Pressure Sensors: {len(pressure_cols)} points
• Setpoint Controls: {len(setpoint_cols)} points
• Zone Controls: {len(zone_cols)} zones

========================================
🎯 ENVIRONMENTAL PERFORMANCE
========================================
{''.join(results)}

========================================
💡 BUILDING OPTIMIZATION INSIGHTS
========================================

Comfort & Efficiency:
• Maintain optimal temperature ranges for occupant comfort
• Monitor humidity levels for indoor air quality
• Implement adaptive setpoints based on occupancy
• Optimize zone control for energy efficiency

Control Strategies:
• Deploy advanced algorithms for predictive control
• Integrate weather forecasting for proactive adjustments
• Implement demand-controlled ventilation
• Consider thermal mass utilization for load shifting

This analysis supports intelligent building operations and energy optimization
while maintaining optimal occupant comfort and indoor air quality."""

    def process_alarm_data(self, df: pd.DataFrame, filename: str) -> str:
        """Process alarm and event data."""
        alarm_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['alarm', 'alert', 'fault', 'error', 'warning'])]
        priority_cols = [col for col in df.columns if 'priority' in col.lower() or 'level' in col.lower()]
        time_cols = [col for col in df.columns if any(indicator in col.lower() for indicator in ['time', 'date', 'timestamp'])]
        
        # Analyze alarm frequency and types
        if alarm_cols:
            alarm_col = alarm_cols[0]
            alarm_counts = df[alarm_col].value_counts()
            total_alarms = len(df)
            unique_alarms = df[alarm_col].nunique()
            
            # Identify most frequent alarms
            top_alarms = alarm_counts.head(5)
            
            results = f"""
🚨 ALARM SUMMARY:
• Total Alarm Events: {total_alarms:,}
• Unique Alarm Types: {unique_alarms}
• Most Frequent Alarm: {top_alarms.index[0]} ({top_alarms.iloc[0]} occurrences)

🔍 TOP 5 ALARM TYPES:
"""
            for i, (alarm, count) in enumerate(top_alarms.items(), 1):
                percentage = (count / total_alarms) * 100
                results += f"{i}. {alarm}: {count} times ({percentage:.1f}%)\n"
            
        return f"""ALARM & EVENT DATA ANALYSIS REPORT
Source File: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Type: Building Systems Alarms and Events

========================================
🚨 ALARM OVERVIEW
========================================
{results}

========================================
📊 ALARM PATTERN ANALYSIS
========================================

Frequency Analysis:
• High frequency alarms may indicate system issues
• Recurring patterns suggest maintenance needs
• Time-based clustering indicates operational problems

Priority Assessment:
• Critical alarms require immediate attention
• Warning alarms indicate potential issues
• Informational alarms provide system status

========================================
🎯 MAINTENANCE PRIORITIES
========================================

Immediate Actions:
• Address high-frequency critical alarms
• Investigate recurring system faults
• Verify alarm calibration and setpoints

Preventive Measures:
• Schedule maintenance for problem equipment
• Update alarm thresholds if needed
• Implement predictive maintenance strategies

This analysis helps prioritize maintenance activities and improve
system reliability through proactive alarm management."""
    
    def process_csv_file(self, file_path: Path) -> str:
        """Main method to process any energy-related CSV file."""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            if df.empty:
                return f"ERROR: Empty CSV file - {file_path.name}"
            
            # Detect energy data type
            data_type = self.detect_energy_data_type(df)
            
            # Process based on detected type
            if data_type == "energy_meter":
                return self.process_energy_meter_data(df, file_path.name)
            elif data_type == "hvac_energy":
                return self.process_hvac_energy_data(df, file_path.name)
            elif data_type == "electrical_parameters":
                return self.process_electrical_parameters_data(df, file_path.name)
            elif data_type == "building_automation":
                return self.process_building_automation_data(df, file_path.name)
            elif data_type == "alarm_data":
                return self.process_alarm_data(df, file_path.name)
            elif data_type == "general_energy":
                return self.process_energy_meter_data(df, file_path.name)  # Default to energy meter processing
            else:
                return f"Energy data type '{data_type}' not yet supported for specialized processing."
                
        except Exception as e:
            logger.error(f"Error processing energy CSV file {file_path}: {str(e)}")
            return f"ERROR processing {file_path.name}: {str(e)}"
