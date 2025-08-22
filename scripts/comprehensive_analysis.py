#!/usr/bin/env python3
"""
Comprehensive Data Analysis for PrivateGPT - Captures detailed patterns from large datasets.
Creates rich, detailed reports while maintaining structure for LLM processing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataProcessor:
    def __init__(self, csv_path: str, output_dir: str = "comprehensive_analysis"):
        self.csv_path = Path(csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_and_analyze_data(self):
        """Load data and perform comprehensive analysis."""
        logger.info(f"Loading comprehensive data from {self.csv_path}")
        df = pd.read_csv(self.csv_path, low_memory=False)
        
        # Clean and prepare data
        df['SampleValue'] = pd.to_numeric(df['SampleValue'], errors='coerce')
        df = df.dropna(subset=['SampleValue'])
        
        # Parse time information
        df['TimeOfSample'] = pd.to_datetime(df['TimeOfSample'], errors='coerce')
        df = df.sort_values('TimeOfSample').reset_index(drop=True)
        
        logger.info(f"Processing {len(df)} valid records")
        return df
    
    def create_detailed_time_series_report(self, df):
        """Create detailed time-series analysis report."""
        device_id = df['DeviceSID'].iloc[0]
        values = df['SampleValue']
        times = df['TimeOfSample']
        
        # Time range analysis
        start_time = times.min()
        end_time = times.max()
        duration = end_time - start_time
        
        report = f"""COMPREHENSIVE TIME-SERIES ANALYSIS REPORT
Device ID: {device_id}
Analysis Period: {start_time} to {end_time}
Duration: {duration}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

========================================
📊 DATASET OVERVIEW
========================================

Data Characteristics:
• Total Measurements: {len(values):,}
• Recording Period: {duration.days} days, {duration.seconds//3600} hours
• Average Sampling Rate: {len(values)/duration.total_seconds()*3600:.1f} readings/hour
• Data Completeness: {len(df)/len(df)*100:.1f}%

Value Distribution:
• Minimum Value: {values.min():.3f}
• Maximum Value: {values.max():.3f}
• Mean Value: {values.mean():.3f}
• Median Value: {values.median():.3f}
• Standard Deviation: {values.std():.3f}
• Coefficient of Variation: {values.std()/values.mean()*100:.1f}%

Quartile Analysis:
• Q1 (25th percentile): {values.quantile(0.25):.3f}
• Q2 (50th percentile): {values.quantile(0.50):.3f}
• Q3 (75th percentile): {values.quantile(0.75):.3f}
• Interquartile Range: {values.quantile(0.75) - values.quantile(0.25):.3f}

========================================
📈 TEMPORAL PATTERN ANALYSIS
========================================
"""
        
        # Add hourly pattern analysis
        if not times.isna().all():
            df_time = df.copy()
            df_time['Hour'] = df_time['TimeOfSample'].dt.hour
            df_time['DayOfWeek'] = df_time['TimeOfSample'].dt.dayofweek
            df_time['Month'] = df_time['TimeOfSample'].dt.month
            
            hourly_stats = df_time.groupby('Hour')['SampleValue'].agg(['mean', 'std', 'count'])
            daily_stats = df_time.groupby('DayOfWeek')['SampleValue'].agg(['mean', 'std', 'count'])
            
            report += "Hourly Patterns:\n"
            for hour in range(24):
                if hour in hourly_stats.index:
                    stats = hourly_stats.loc[hour]
                    report += f"• {hour:02d}:00 - Avg: {stats['mean']:.2f}, StdDev: {stats['std']:.2f}, Count: {stats['count']}\n"
            
            report += "\nDaily Patterns (0=Monday, 6=Sunday):\n"
            for day in range(7):
                if day in daily_stats.index:
                    stats = daily_stats.loc[day]
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    report += f"• {day_names[day]}: Avg: {stats['mean']:.2f}, StdDev: {stats['std']:.2f}, Count: {stats['count']}\n"
        
        return report
    
    def create_statistical_analysis_report(self, df):
        """Create detailed statistical analysis."""
        values = df['SampleValue']
        
        # Advanced statistical analysis
        from scipy import stats
        
        # Distribution analysis
        skewness = stats.skew(values)
        kurtosis = stats.kurtosis(values)
        
        # Normality test
        shapiro_stat, shapiro_p = stats.shapiro(values[:5000] if len(values) > 5000 else values)
        
        report = f"""
========================================
📊 ADVANCED STATISTICAL ANALYSIS
========================================

Distribution Characteristics:
• Skewness: {skewness:.3f} ({'Right-skewed' if skewness > 0.5 else 'Left-skewed' if skewness < -0.5 else 'Approximately symmetric'})
• Kurtosis: {kurtosis:.3f} ({'Heavy-tailed' if kurtosis > 0 else 'Light-tailed'})
• Normality Test (Shapiro-Wilk): p-value = {shapiro_p:.6f} ({'Normal' if shapiro_p > 0.05 else 'Non-normal'} distribution)

Percentile Analysis:
"""
        
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            report += f"• {p}th percentile: {values.quantile(p/100):.3f}\n"
        
        # Moving statistics
        window_sizes = [100, 500, 1000]
        report += "\nMoving Average Analysis:\n"
        for window in window_sizes:
            if len(values) >= window:
                ma = values.rolling(window=window).mean()
                report += f"• {window}-point MA: Current = {ma.iloc[-1]:.3f}, Trend = {'Increasing' if ma.iloc[-1] > ma.iloc[-window//2] else 'Decreasing'}\n"
        
        return report
    
    def create_operational_insights_report(self, df):
        """Create operational insights and anomaly analysis."""
        values = df['SampleValue']
        
        # Control limits
        mean_val = values.mean()
        std_val = values.std()
        ucl = mean_val + 3 * std_val
        lcl = mean_val - 3 * std_val
        
        # Anomaly detection
        anomalies = values[(values > ucl) | (values < lcl)]
        high_anomalies = values[values > ucl]
        low_anomalies = values[values < lcl]
        
        # Consecutive runs analysis
        above_mean = (values > mean_val).astype(int)
        run_lengths = []
        current_run = 1
        for i in range(1, len(above_mean)):
            if above_mean.iloc[i] == above_mean.iloc[i-1]:
                current_run += 1
            else:
                run_lengths.append(current_run)
                current_run = 1
        run_lengths.append(current_run)
        
        longest_run = max(run_lengths) if run_lengths else 0
        
        report = f"""
========================================
🔍 OPERATIONAL INSIGHTS & ANOMALIES
========================================

Control Chart Analysis:
• Center Line (Mean): {mean_val:.3f}
• Upper Control Limit (+3σ): {ucl:.3f}
• Lower Control Limit (-3σ): {lcl:.3f}
• Total Out-of-Control Points: {len(anomalies)} ({len(anomalies)/len(values)*100:.2f}%)
• High Anomalies (>{ucl:.1f}): {len(high_anomalies)}
• Low Anomalies (<{lcl:.1f}): {len(low_anomalies)}

Process Stability:
• Longest Run Above/Below Mean: {longest_run} consecutive points
• Process Status: {'Stable' if len(anomalies)/len(values) < 0.01 else 'Unstable'}

Value Zones Analysis:
• Zone A (>2σ): {len(values[values > mean_val + 2*std_val])} points ({len(values[values > mean_val + 2*std_val])/len(values)*100:.1f}%)
• Zone B (1-2σ): {len(values[(values > mean_val + std_val) & (values <= mean_val + 2*std_val)])} points
• Zone C (0-1σ): {len(values[(values > mean_val) & (values <= mean_val + std_val)])} points
• Normal Zone: {len(values[abs(values - mean_val) <= std_val])} points ({len(values[abs(values - mean_val) <= std_val])/len(values)*100:.1f}%)
"""
        
        # Trend analysis
        if len(values) >= 1000:
            # Split into segments for trend analysis
            segment_size = len(values) // 10
            trends = []
            for i in range(0, len(values), segment_size):
                segment = values.iloc[i:i+segment_size]
                if len(segment) > 10:
                    x = np.arange(len(segment))
                    slope = np.polyfit(x, segment, 1)[0]
                    trends.append(slope)
            
            report += f"\nTrend Analysis (10 segments):\n"
            for i, trend in enumerate(trends):
                direction = "Increasing" if trend > 0.01 else "Decreasing" if trend < -0.01 else "Stable"
                report += f"• Segment {i+1}: Slope = {trend:.4f} ({direction})\n"
        
        return report
    
    def create_engineering_analysis_report(self, df):
        """Create engineering-specific analysis."""
        device_id = df['DeviceSID'].iloc[0]
        values = df['SampleValue']
        
        # Engineering unit analysis
        eng_unit = df['EngUnitID'].iloc[0] if 'EngUnitID' in df.columns else 'Unknown'
        trend_log_sid = df['TrendLogSID'].iloc[0] if 'TrendLogSID' in df.columns else 'Unknown'
        
        # Rate of change analysis
        rate_of_change = values.diff()
        max_positive_change = rate_of_change.max()
        max_negative_change = rate_of_change.min()
        avg_change_rate = rate_of_change.abs().mean()
        
        # Stability metrics
        stability_index = values.std() / values.mean() if values.mean() != 0 else float('inf')
        
        report = f"""
========================================
🔧 ENGINEERING ANALYSIS
========================================

Equipment Information:
• Device ID: {device_id}
• Trend Log SID: {trend_log_sid}
• Engineering Unit ID: {eng_unit}
• Measurement Type: {'Continuous Process Variable' if len(values) > 10000 else 'Batch/Discrete Measurement'}

Rate of Change Analysis:
• Maximum Positive Change: {max_positive_change:.3f} units/reading
• Maximum Negative Change: {max_negative_change:.3f} units/reading
• Average Change Rate: {avg_change_rate:.3f} units/reading
• Stability Index (CV): {stability_index:.3f} ({'Stable' if stability_index < 0.1 else 'Moderate' if stability_index < 0.3 else 'Unstable'})

Operating Ranges:
• Normal Operating Range (±1σ): {values.mean() - values.std():.2f} to {values.mean() + values.std():.2f}
• Acceptable Range (±2σ): {values.mean() - 2*values.std():.2f} to {values.mean() + 2*values.std():.2f}
• Alert Threshold (±3σ): {values.mean() - 3*values.std():.2f} to {values.mean() + 3*values.std():.2f}

Performance Metrics:
• Process Capability Estimate: {(6*values.std())/(values.max()-values.min()):.3f}
• Signal-to-Noise Ratio: {values.mean()/values.std():.2f}
• Dynamic Range: {(values.max()-values.min())/values.mean()*100:.1f}% of mean
"""
        
        return report
    
    def create_maintenance_recommendations(self, df):
        """Create detailed maintenance recommendations."""
        values = df['SampleValue']
        
        # Trend analysis for maintenance
        recent_data = values.tail(1000) if len(values) > 1000 else values
        overall_trend = np.polyfit(range(len(recent_data)), recent_data, 1)[0]
        
        # Variability analysis
        recent_std = recent_data.std()
        historical_std = values.std()
        variability_change = (recent_std - historical_std) / historical_std * 100
        
        report = f"""
========================================
🔧 PREDICTIVE MAINTENANCE RECOMMENDATIONS
========================================

Current Status Assessment:
• Overall Trend: {'Increasing' if overall_trend > 0.01 else 'Decreasing' if overall_trend < -0.01 else 'Stable'} ({overall_trend:.4f} units/reading)
• Variability Change: {variability_change:+.1f}% vs historical average
• Risk Level: {'HIGH' if abs(overall_trend) > 0.1 or abs(variability_change) > 50 else 'MEDIUM' if abs(overall_trend) > 0.05 or abs(variability_change) > 25 else 'LOW'}

Maintenance Actions:

IMMEDIATE (Next 7 days):
"""
        
        if abs(overall_trend) > 0.1:
            report += f"• URGENT: Investigate {'increasing' if overall_trend > 0 else 'decreasing'} trend (slope: {overall_trend:.4f})\n"
        if abs(variability_change) > 50:
            report += f"• URGENT: Process variability changed by {variability_change:+.1f}% - check equipment condition\n"
        if len(values[values > values.mean() + 3*values.std()]) > len(values) * 0.01:
            report += "• URGENT: High number of out-of-control readings - inspect sensors and calibration\n"
        
        report += "\nSHORT TERM (Next 30 days):\n"
        if abs(overall_trend) > 0.05:
            report += "• Schedule detailed equipment inspection\n"
        if values.std()/values.mean() > 0.3:
            report += "• Review process control parameters - high variability detected\n"
        
        report += "• Verify sensor calibration\n• Check data logging system integrity\n"
        
        report += "\nLONG TERM (Next 90 days):\n"
        report += "• Establish baseline performance metrics\n"
        report += "• Implement automated anomaly detection\n"
        report += "• Schedule preventive maintenance based on trends\n"
        
        # Prediction
        if len(values) >= 100:
            next_30_predictions = values.iloc[-1] + overall_trend * np.arange(1, 31)
            report += f"\nPredictive Forecast (Next 30 readings):\n"
            report += f"• Expected Range: {next_30_predictions.min():.2f} to {next_30_predictions.max():.2f}\n"
            report += f"• Trend Direction: {'Upward' if overall_trend > 0 else 'Downward' if overall_trend < 0 else 'Stable'}\n"
            
            if any(next_30_predictions > values.mean() + 3*values.std()):
                report += "• ⚠️ WARNING: Predictions exceed upper control limit\n"
            if any(next_30_predictions < values.mean() - 3*values.std()):
                report += "• ⚠️ WARNING: Predictions below lower control limit\n"
        
        return report
    
    def save_comprehensive_analysis(self, reports):
        """Save all analysis reports."""
        logger.info("Saving comprehensive analysis...")
        
        # Combine all reports into one comprehensive document
        combined_report = f"""COMPREHENSIVE INDUSTRIAL DATA ANALYSIS REPORT
{'='*80}

{reports['time_series']}

{reports['statistical']}

{reports['operational']}

{reports['engineering']}

{reports['maintenance']}

{'='*80}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Source: Industrial Sensor/Control System
Analysis Type: Comprehensive Predictive Analytics
{'='*80}
"""
        
        # Save main comprehensive report
        main_report_path = self.output_dir / "comprehensive_industrial_analysis.txt"
        with open(main_report_path, 'w', encoding='utf-8') as f:
            f.write(combined_report)
        
        # Save individual focused reports for specific queries
        focused_reports = {
            'maintenance_focus.txt': f"MAINTENANCE-FOCUSED ANALYSIS\n{reports['maintenance']}\n{reports['operational']}",
            'engineering_focus.txt': f"ENGINEERING ANALYSIS\n{reports['engineering']}\n{reports['statistical']}",
            'operational_focus.txt': f"OPERATIONAL INSIGHTS\n{reports['operational']}\n{reports['time_series']}"
        }
        
        paths = [main_report_path]
        for filename, content in focused_reports.items():
            path = self.output_dir / filename
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            paths.append(path)
        
        logger.info(f"Generated {len(paths)} comprehensive analysis files")
        return paths
    
    def process(self):
        """Main processing pipeline."""
        logger.info("Starting comprehensive data analysis...")
        
        # Load data
        df = self.load_and_analyze_data()
        
        # Generate all analysis reports
        reports = {
            'time_series': self.create_detailed_time_series_report(df),
            'statistical': self.create_statistical_analysis_report(df),
            'operational': self.create_operational_insights_report(df),
            'engineering': self.create_engineering_analysis_report(df),
            'maintenance': self.create_maintenance_recommendations(df)
        }
        
        # Save comprehensive analysis
        paths = self.save_comprehensive_analysis(reports)
        
        logger.info("✅ Comprehensive analysis complete!")
        for path in paths:
            logger.info(f"📄 Generated: {path}")
        
        return paths

def main():
    """Main entry point."""
    csv_file = "Trend-Raw-Data_1.csv"
    
    if not Path(csv_file).exists():
        logger.error(f"CSV file not found: {csv_file}")
        return
    
    try:
        processor = ComprehensiveDataProcessor(csv_file)
        paths = processor.process()
        
        print("\n" + "="*80)
        print("🎉 COMPREHENSIVE INDUSTRIAL ANALYSIS COMPLETE!")
        print("="*80)
        print("📊 Generated Detailed Analysis Files:")
        for path in paths:
            print(f"   • {path}")
        
        print("\n💡 Upload to PrivateGPT for detailed insights:")
        print("   • 'Provide detailed maintenance recommendations for Device 3'")
        print("   • 'Analyze the time-series patterns and explain anomalies'")
        print("   • 'What are the engineering specifications and operating ranges?'")
        print("   • 'Generate a comprehensive equipment health report'")
        print("   • 'Explain the statistical control analysis results'")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()
