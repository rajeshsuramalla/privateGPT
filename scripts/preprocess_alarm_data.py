#!/usr/bin/env python3
"""
Preprocessing script for alarm/trend data for PrivateGPT ingestion.
Converts raw CSV data into structured narratives for efficient LLM processing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrendDataPreprocessor:
    def __init__(self, csv_path: str, output_dir: str = "processed_data"):
        self.csv_path = Path(csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_data(self):
        """Load CSV data with proper handling."""
        logger.info(f"Loading data from {self.csv_path}")
        try:
            # Read CSV with proper handling of quotes and data types
            df = pd.read_csv(self.csv_path, low_memory=False)
            logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def analyze_data_patterns(self, df):
        """Analyze data patterns and create summaries."""
        logger.info("Analyzing data patterns...")
        
        # Convert SampleValue to numeric, handling errors
        df['SampleValue'] = pd.to_numeric(df['SampleValue'], errors='coerce')
        
        # Group by DeviceSID for device-level analysis
        device_summaries = []
        
        for device_id in df['DeviceSID'].unique():
            if pd.isna(device_id):
                continue
                
            device_data = df[df['DeviceSID'] == device_id].copy()
            
            # Basic statistics
            sample_values = device_data['SampleValue'].dropna()
            
            if len(sample_values) == 0:
                continue
                
            summary = {
                'device_id': device_id,
                'total_readings': len(device_data),
                'value_range': f"{sample_values.min():.2f} to {sample_values.max():.2f}",
                'avg_value': sample_values.mean(),
                'std_value': sample_values.std(),
                'trend_log_sid': device_data['TrendLogSID'].iloc[0] if not device_data['TrendLogSID'].empty else 'Unknown',
                'eng_unit_id': device_data['EngUnitID'].iloc[0] if not device_data['EngUnitID'].empty else 'Unknown'
            }
            
            # Detect anomalies (values beyond 2 standard deviations)
            if len(sample_values) > 3:
                mean_val = summary['avg_value']
                std_val = summary['std_value']
                anomalies = sample_values[(sample_values < mean_val - 2*std_val) | 
                                        (sample_values > mean_val + 2*std_val)]
                summary['anomaly_count'] = len(anomalies)
                summary['anomaly_percentage'] = (len(anomalies) / len(sample_values)) * 100
            else:
                summary['anomaly_count'] = 0
                summary['anomaly_percentage'] = 0
            
            # Detect trend patterns
            if len(sample_values) > 10:
                # Simple trend detection using linear regression
                x = np.arange(len(sample_values))
                slope = np.polyfit(x, sample_values, 1)[0]
                if abs(slope) > std_val * 0.1:  # Significant trend
                    if slope > 0:
                        summary['trend'] = f"Increasing (slope: {slope:.4f})"
                    else:
                        summary['trend'] = f"Decreasing (slope: {slope:.4f})"
                else:
                    summary['trend'] = "Stable"
            else:
                summary['trend'] = "Insufficient data"
            
            device_summaries.append(summary)
        
        return device_summaries
    
    def create_narrative_summaries(self, device_summaries):
        """Convert device summaries into narrative text for LLM."""
        logger.info("Creating narrative summaries...")
        
        narratives = []
        
        for summary in device_summaries:
            device_id = summary['device_id']
            
            # Create a structured narrative
            narrative = f"""Device Analysis Report - Device ID: {device_id}
            
OPERATIONAL SUMMARY:
- Device {device_id} recorded {summary['total_readings']} sensor readings
- Trend Log ID: {summary['trend_log_sid']} | Engineering Unit: {summary['eng_unit_id']}
- Value Range: {summary['value_range']}
- Average Reading: {summary['avg_value']:.2f} ± {summary['std_value']:.2f}

PERFORMANCE ANALYSIS:
- Trend Pattern: {summary['trend']}
- Data Quality: {summary['anomaly_count']} anomalous readings ({summary['anomaly_percentage']:.1f}% of total)

OPERATIONAL STATUS:
"""
            
            # Add status assessment
            if summary['anomaly_percentage'] > 10:
                narrative += f"- ⚠️ HIGH ALERT: Device {device_id} shows {summary['anomaly_percentage']:.1f}% anomalous readings. Requires immediate inspection.\n"
            elif summary['anomaly_percentage'] > 5:
                narrative += f"- ⚡ CAUTION: Device {device_id} shows {summary['anomaly_percentage']:.1f}% anomalous readings. Monitor closely.\n"
            else:
                narrative += f"- ✅ NORMAL: Device {device_id} operating within normal parameters.\n"
            
            # Add trend assessment
            if "Increasing" in summary['trend'] or "Decreasing" in summary['trend']:
                narrative += f"- 📈 TREND ALERT: Device {device_id} shows {summary['trend'].lower()} pattern. Review operational parameters.\n"
            else:
                narrative += f"- 📊 STABLE: Device {device_id} readings remain stable over time.\n"
            
            narrative += "\n" + "="*80 + "\n"
            narratives.append(narrative)
        
        return narratives
    
    def create_executive_summary(self, device_summaries):
        """Create an executive summary for management overview."""
        total_devices = len(device_summaries)
        high_risk_devices = [s for s in device_summaries if s['anomaly_percentage'] > 10]
        medium_risk_devices = [s for s in device_summaries if 5 < s['anomaly_percentage'] <= 10]
        normal_devices = [s for s in device_summaries if s['anomaly_percentage'] <= 5]
        
        trending_devices = [s for s in device_summaries if "Increasing" in s['trend'] or "Decreasing" in s['trend']]
        
        summary = f"""EXECUTIVE SUMMARY - DEVICE MONITORING REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FLEET OVERVIEW:
- Total Devices Monitored: {total_devices}
- High Risk Devices (>10% anomalies): {len(high_risk_devices)}
- Medium Risk Devices (5-10% anomalies): {len(medium_risk_devices)}
- Normal Operation Devices: {len(normal_devices)}

CRITICAL ALERTS:
"""
        
        if high_risk_devices:
            summary += "🚨 HIGH PRIORITY DEVICES REQUIRING IMMEDIATE ATTENTION:\n"
            for device in high_risk_devices:
                summary += f"  - Device {device['device_id']}: {device['anomaly_percentage']:.1f}% anomalous readings\n"
        else:
            summary += "✅ No high-risk devices identified.\n"
        
        summary += "\nTREND ANALYSIS:\n"
        if trending_devices:
            summary += f"📈 {len(trending_devices)} devices showing significant trends:\n"
            for device in trending_devices[:5]:  # Top 5
                summary += f"  - Device {device['device_id']}: {device['trend']}\n"
        else:
            summary += "📊 All monitored devices showing stable patterns.\n"
        
        summary += f"""
RECOMMENDATIONS:
1. Schedule immediate inspection for {len(high_risk_devices)} high-risk devices
2. Increase monitoring frequency for {len(medium_risk_devices)} medium-risk devices
3. Continue standard monitoring for {len(normal_devices)} normal devices
4. Review trending patterns for {len(trending_devices)} devices showing directional changes

NEXT ACTIONS:
- Prioritize maintenance for devices with >10% anomaly rates
- Investigate root cause of trending patterns
- Update alert thresholds based on operational requirements
"""
        
        return summary
    
    def save_processed_data(self, narratives, executive_summary):
        """Save processed data for PrivateGPT ingestion."""
        logger.info("Saving processed data...")
        
        # Save individual device narratives
        device_report_path = self.output_dir / "device_analysis_report.txt"
        with open(device_report_path, 'w', encoding='utf-8') as f:
            f.write("DEVICE MONITORING ANALYSIS REPORT\n")
            f.write("="*50 + "\n\n")
            f.write('\n\n'.join(narratives))
        
        # Save executive summary
        exec_summary_path = self.output_dir / "executive_summary.txt"
        with open(exec_summary_path, 'w', encoding='utf-8') as f:
            f.write(executive_summary)
        
        logger.info(f"Processed data saved to:")
        logger.info(f"  - Device Analysis: {device_report_path}")
        logger.info(f"  - Executive Summary: {exec_summary_path}")
        
        return device_report_path, exec_summary_path
    
    def process(self):
        """Main processing pipeline."""
        logger.info("Starting data preprocessing pipeline...")
        
        # Load and analyze data
        df = self.load_data()
        device_summaries = self.analyze_data_patterns(df)
        
        # Create narratives
        narratives = self.create_narrative_summaries(device_summaries)
        executive_summary = self.create_executive_summary(device_summaries)
        
        # Save processed data
        device_path, summary_path = self.save_processed_data(narratives, executive_summary)
        
        logger.info("✅ Preprocessing complete!")
        logger.info(f"📁 Ingest these files into PrivateGPT:")
        logger.info(f"   1. {device_path}")
        logger.info(f"   2. {summary_path}")
        
        return device_path, summary_path

def main():
    """Main entry point."""
    csv_file = "Trend-Raw-Data_1.csv"  # Your CSV file
    
    if not Path(csv_file).exists():
        logger.error(f"CSV file not found: {csv_file}")
        return
    
    try:
        preprocessor = TrendDataPreprocessor(csv_file)
        device_path, summary_path = preprocessor.process()
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Your data is ready for PrivateGPT!")
        print("="*60)
        print(f"📄 Device Analysis Report: {device_path}")
        print(f"📋 Executive Summary: {summary_path}")
        print("\n💡 Next Steps:")
        print("1. Open PrivateGPT web interface")
        print("2. Upload both generated .txt files")
        print("3. Wait for ingestion to complete")
        print("4. Ask questions like:")
        print("   • 'Which devices need immediate attention?'")
        print("   • 'Show me devices with trending patterns'")
        print("   • 'Generate a maintenance priority list'")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()
