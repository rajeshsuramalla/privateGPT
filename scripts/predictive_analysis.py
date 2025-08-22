#!/usr/bin/env python3
"""
Enhanced Predictive Analytics Preprocessing for PrivateGPT.
Creates detailed predictive reports with time-series analysis, forecasting, and operational insights.
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

class PredictiveAnalysisPreprocessor:
    def __init__(self, csv_path: str, output_dir: str = "predictive_analysis"):
        self.csv_path = Path(csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_and_prepare_data(self):
        """Load and prepare data with time analysis."""
        logger.info(f"Loading data from {self.csv_path}")
        df = pd.read_csv(self.csv_path, low_memory=False)
        
        # Convert to numeric and handle time
        df['SampleValue'] = pd.to_numeric(df['SampleValue'], errors='coerce')
        
        # Sort by time to enable time-series analysis
        df = df.sort_values('TimeOfSample').reset_index(drop=True)
        
        # Add sequence number for time-based analysis
        df['Sequence'] = range(len(df))
        
        logger.info(f"Loaded {len(df)} records spanning time series data")
        return df
    
    def perform_predictive_analysis(self, df):
        """Perform comprehensive predictive analysis."""
        logger.info("Performing predictive analysis...")
        
        device_id = df['DeviceSID'].iloc[0]
        values = df['SampleValue'].dropna()
        
        # Basic statistics
        analysis = {
            'device_id': device_id,
            'total_readings': len(values),
            'mean_value': values.mean(),
            'std_value': values.std(),
            'min_value': values.min(),
            'max_value': values.max(),
            'range_value': values.max() - values.min()
        }
        
        # Quartile analysis for operational zones
        q1, q2, q3 = values.quantile([0.25, 0.50, 0.75])
        analysis.update({
            'q1': q1, 'median': q2, 'q3': q3,
            'iqr': q3 - q1
        })
        
        # Time-based pattern analysis
        analysis.update(self._analyze_time_patterns(values))
        
        # Variability and stability analysis
        analysis.update(self._analyze_stability(values))
        
        # Predictive insights
        analysis.update(self._generate_predictions(values))
        
        # Risk assessment
        analysis.update(self._assess_risks(values, analysis))
        
        return analysis
    
    def _analyze_time_patterns(self, values):
        """Analyze time-based patterns and trends."""
        patterns = {}
        
        # Moving averages for trend detection
        if len(values) >= 100:
            short_ma = values.rolling(window=50).mean()
            long_ma = values.rolling(window=200).mean()
            
            # Trend analysis
            recent_short = short_ma.tail(10).mean()
            recent_long = long_ma.tail(10).mean()
            
            if recent_short > recent_long * 1.05:
                patterns['trend_direction'] = "Upward trend detected"
                patterns['trend_strength'] = "Strong" if recent_short > recent_long * 1.1 else "Moderate"
            elif recent_short < recent_long * 0.95:
                patterns['trend_direction'] = "Downward trend detected"
                patterns['trend_strength'] = "Strong" if recent_short < recent_long * 0.9 else "Moderate"
            else:
                patterns['trend_direction'] = "Stable pattern"
                patterns['trend_strength'] = "Stable"
        
        # Volatility analysis
        rolling_std = values.rolling(window=100).std()
        patterns['volatility_trend'] = "Increasing" if rolling_std.tail(50).mean() > rolling_std.head(50).mean() else "Decreasing"
        
        # Cycle detection (simplified)
        if len(values) >= 1000:
            # Look for repeating patterns
            autocorr_lags = [100, 200, 500, 1000]
            max_autocorr = 0
            best_lag = 0
            
            for lag in autocorr_lags:
                if lag < len(values):
                    autocorr = np.corrcoef(values[:-lag], values[lag:])[0, 1]
                    if not np.isnan(autocorr) and abs(autocorr) > max_autocorr:
                        max_autocorr = abs(autocorr)
                        best_lag = lag
            
            if max_autocorr > 0.3:
                patterns['cyclical_pattern'] = f"Potential {best_lag}-reading cycle detected (correlation: {max_autocorr:.3f})"
            else:
                patterns['cyclical_pattern'] = "No significant cyclical patterns detected"
        
        return patterns
    
    def _analyze_stability(self, values):
        """Analyze operational stability and control limits."""
        stability = {}
        
        # Control limits (3-sigma)
        mean_val = values.mean()
        std_val = values.std()
        
        ucl = mean_val + 3 * std_val  # Upper Control Limit
        lcl = mean_val - 3 * std_val  # Lower Control Limit
        
        out_of_control = values[(values > ucl) | (values < lcl)]
        
        stability.update({
            'control_mean': mean_val,
            'upper_control_limit': ucl,
            'lower_control_limit': lcl,
            'out_of_control_points': len(out_of_control),
            'control_stability': "In Control" if len(out_of_control) < len(values) * 0.01 else "Out of Control"
        })
        
        # Process capability analysis
        if len(values) >= 1000:
            # Assuming specification limits (you can adjust these)
            usl = values.quantile(0.99)  # Upper Spec Limit
            lsl = values.quantile(0.01)  # Lower Spec Limit
            
            cp = (usl - lsl) / (6 * std_val)  # Process Capability
            cpk = min((usl - mean_val), (mean_val - lsl)) / (3 * std_val)  # Process Capability Index
            
            stability.update({
                'process_capability_cp': cp,
                'process_capability_cpk': cpk,
                'capability_assessment': self._assess_capability(cp, cpk)
            })
        
        return stability
    
    def _assess_capability(self, cp, cpk):
        """Assess process capability."""
        if cpk >= 1.33:
            return "Excellent - Process highly capable"
        elif cpk >= 1.0:
            return "Good - Process capable"
        elif cpk >= 0.67:
            return "Marginal - Process improvement needed"
        else:
            return "Poor - Immediate process improvement required"
    
    def _generate_predictions(self, values):
        """Generate predictive insights and forecasts."""
        predictions = {}
        
        # Simple trend-based prediction
        if len(values) >= 100:
            recent_trend = np.polyfit(range(len(values[-100:])), values[-100:], 1)[0]
            
            # Predict next 50 readings
            next_values = values.iloc[-1] + recent_trend * np.arange(1, 51)
            
            predictions.update({
                'trend_slope': recent_trend,
                'predicted_next_value': values.iloc[-1] + recent_trend,
                'predicted_50_reading_avg': next_values.mean(),
                'prediction_confidence': "High" if abs(recent_trend) < values.std() * 0.1 else "Moderate"
            })
            
            # Maintenance prediction
            if recent_trend < -0.1:
                predictions['maintenance_alert'] = "Declining trend detected - consider proactive maintenance"
            elif recent_trend > 0.1:
                predictions['maintenance_alert'] = "Increasing trend detected - monitor for potential overheating/pressure build-up"
            else:
                predictions['maintenance_alert'] = "No immediate maintenance concerns based on trend"
        
        # Anomaly prediction
        recent_variability = values[-100:].std() if len(values) >= 100 else values.std()
        historical_variability = values.std()
        
        if recent_variability > historical_variability * 1.5:
            predictions['anomaly_forecast'] = "Increased variability suggests potential equipment issues"
        elif recent_variability < historical_variability * 0.5:
            predictions['anomaly_forecast'] = "Reduced variability - equipment running very consistently"
        else:
            predictions['anomaly_forecast'] = "Normal operational variability expected"
        
        return predictions
    
    def _assess_risks(self, values, analysis):
        """Comprehensive risk assessment."""
        risks = {}
        
        # Operational risk levels
        risk_score = 0
        risk_factors = []
        
        # Control stability risk
        if analysis.get('control_stability') == "Out of Control":
            risk_score += 30
            risk_factors.append("Process out of statistical control")
        
        # Trend risk
        trend_slope = analysis.get('trend_slope', 0)
        if abs(trend_slope) > values.std() * 0.1:
            risk_score += 20
            risk_factors.append(f"Significant trend detected (slope: {trend_slope:.4f})")
        
        # Variability risk
        if values.std() > values.mean() * 0.5:
            risk_score += 15
            risk_factors.append("High process variability")
        
        # Capability risk
        cpk = analysis.get('process_capability_cpk', 1.0)
        if cpk < 1.0:
            risk_score += 25
            risk_factors.append("Process capability below acceptable threshold")
        
        # Overall risk assessment
        if risk_score >= 50:
            risk_level = "HIGH RISK"
            recommended_action = "Immediate intervention required"
        elif risk_score >= 25:
            risk_level = "MEDIUM RISK"
            recommended_action = "Increased monitoring and planned maintenance"
        else:
            risk_level = "LOW RISK"
            recommended_action = "Continue normal operations"
        
        risks.update({
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommended_action': recommended_action
        })
        
        return risks
    
    def create_predictive_narrative(self, analysis):
        """Create comprehensive predictive narrative."""
        device_id = analysis['device_id']
        
        narrative = f"""PREDICTIVE ANALYTICS REPORT - Device {device_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

========================================
📊 OPERATIONAL PERFORMANCE SUMMARY
========================================

Device {device_id} Analysis:
• Total Data Points: {analysis['total_readings']:,}
• Operational Range: {analysis['min_value']:.2f} to {analysis['max_value']:.2f} (Range: {analysis['range_value']:.2f})
• Performance Mean: {analysis['mean_value']:.2f} ± {analysis['std_value']:.2f}
• Median Value: {analysis['median']:.2f}

📈 STATISTICAL CONTROL ANALYSIS:
• Control Limits: {analysis.get('lower_control_limit', 0):.2f} to {analysis.get('upper_control_limit', 0):.2f}
• Control Status: {analysis.get('control_stability', 'Unknown')}
• Out-of-Control Points: {analysis.get('out_of_control_points', 0)}
"""

        if 'process_capability_cp' in analysis:
            narrative += f"""
🎯 PROCESS CAPABILITY:
• Cp (Process Capability): {analysis['process_capability_cp']:.3f}
• Cpk (Capability Index): {analysis['process_capability_cpk']:.3f}
• Assessment: {analysis['capability_assessment']}
"""

        narrative += f"""
📊 TREND ANALYSIS:
• Direction: {analysis.get('trend_direction', 'Not available')}
• Strength: {analysis.get('trend_strength', 'Not available')}
• Volatility: {analysis.get('volatility_trend', 'Not available')}
• Pattern: {analysis.get('cyclical_pattern', 'Not analyzed')}
"""

        if 'trend_slope' in analysis:
            narrative += f"""
🔮 PREDICTIVE FORECASTING:
• Trend Slope: {analysis['trend_slope']:.6f} units per reading
• Next Reading Prediction: {analysis['predicted_next_value']:.2f}
• 50-Reading Average Forecast: {analysis['predicted_50_reading_avg']:.2f}
• Confidence Level: {analysis['prediction_confidence']}

🔧 MAINTENANCE INSIGHTS:
• {analysis['maintenance_alert']}
• Anomaly Forecast: {analysis['anomaly_forecast']}
"""

        narrative += f"""
⚠️ RISK ASSESSMENT:
• Risk Level: {analysis['risk_level']}
• Risk Score: {analysis['risk_score']}/100
• Recommended Action: {analysis['recommended_action']}
"""

        if analysis['risk_factors']:
            narrative += "\n• Critical Risk Factors:\n"
            for factor in analysis['risk_factors']:
                narrative += f"  - {factor}\n"

        narrative += f"""

📋 OPERATIONAL RECOMMENDATIONS:

1. IMMEDIATE ACTIONS:
   • {analysis['recommended_action']}
   • Monitor for values outside control limits ({analysis.get('lower_control_limit', 0):.1f} - {analysis.get('upper_control_limit', 0):.1f})

2. PREDICTIVE MAINTENANCE:
   • Based on trend analysis: {analysis.get('maintenance_alert', 'No specific recommendations')}
   • Schedule inspection if risk level is MEDIUM or HIGH

3. OPTIMIZATION OPPORTUNITIES:
   • Target operational range: {analysis['q1']:.1f} - {analysis['q3']:.1f} (IQR)
   • Focus on reducing variability if std > {analysis['mean_value'] * 0.1:.1f}

4. MONITORING PRIORITIES:
   • Watch for trend changes (current slope: {analysis.get('trend_slope', 0):.6f})
   • Alert if volatility increases beyond current levels
   • Track process capability metrics

========================================
DEVICE STATUS: {analysis['risk_level']}
NEXT REVIEW: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
========================================
"""
        
        return narrative
    
    def create_executive_dashboard(self, analysis):
        """Create executive-level dashboard summary."""
        risk_level = analysis['risk_level']
        device_id = analysis['device_id']
        
        dashboard = f"""EXECUTIVE DASHBOARD - PREDICTIVE ANALYTICS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 FLEET STATUS OVERVIEW:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Device {device_id} Performance Summary:
• Operational Status: {risk_level}
• Performance Score: {100 - analysis['risk_score']}/100
• Process Capability: {analysis.get('capability_assessment', 'Not assessed')}
• Maintenance Priority: {analysis['recommended_action']}

📊 KEY PERFORMANCE INDICATORS:

Current Performance:
├─ Mean Value: {analysis['mean_value']:.1f}
├─ Variability: {analysis['std_value']:.1f} ({analysis['std_value']/analysis['mean_value']*100:.1f}% CV)
├─ Control Status: {analysis.get('control_stability', 'Unknown')}
└─ Trend: {analysis.get('trend_direction', 'Not available')}

Predictive Insights:
├─ Next Value Forecast: {analysis.get('predicted_next_value', 'N/A')}
├─ Trend Direction: {analysis.get('trend_strength', 'Not available')}
├─ Maintenance Alert: {analysis.get('maintenance_alert', 'No alerts')[:50]}...
└─ Anomaly Risk: {analysis.get('anomaly_forecast', 'Not assessed')[:50]}...

💼 EXECUTIVE ACTIONS REQUIRED:

Priority Level: {risk_level}
"""

        if risk_level == "HIGH RISK":
            dashboard += """
🚨 IMMEDIATE ATTENTION REQUIRED:
• Schedule emergency maintenance review
• Implement enhanced monitoring protocols
• Consider backup equipment deployment
"""
        elif risk_level == "MEDIUM RISK":
            dashboard += """
⚠️ PLANNED INTERVENTION RECOMMENDED:
• Schedule maintenance within next planning cycle
• Increase monitoring frequency
• Prepare contingency plans
"""
        else:
            dashboard += """
✅ NOMINAL OPERATIONS:
• Continue standard maintenance schedule
• Maintain current monitoring levels
• Good baseline for comparative analysis
"""

        dashboard += f"""
📈 BUSINESS IMPACT ASSESSMENT:
• Operational Efficiency: {analysis.get('process_capability_cpk', 1.0)*100:.0f}%
• Reliability Index: {max(0, 100-analysis['risk_score'])}/100
• Maintenance Cost Optimization: {"High" if analysis['risk_score'] < 25 else "Medium" if analysis['risk_score'] < 50 else "Low"}

🎯 STRATEGIC RECOMMENDATIONS:
1. Continue data collection for trend validation
2. Implement predictive maintenance scheduling
3. Consider automation for real-time monitoring
4. Benchmark against industry standards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Review: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')} | Generated by Predictive Analytics Engine
"""
        
        return dashboard
    
    def save_analysis(self, narrative, dashboard):
        """Save the predictive analysis reports."""
        logger.info("Saving predictive analysis reports...")
        
        # Save detailed narrative
        narrative_path = self.output_dir / "predictive_analysis_report.txt"
        with open(narrative_path, 'w', encoding='utf-8') as f:
            f.write(narrative)
        
        # Save executive dashboard
        dashboard_path = self.output_dir / "executive_dashboard.txt"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard)
        
        logger.info(f"Reports saved:")
        logger.info(f"  • Predictive Analysis: {narrative_path}")
        logger.info(f"  • Executive Dashboard: {dashboard_path}")
        
        return narrative_path, dashboard_path
    
    def process(self):
        """Main processing pipeline."""
        logger.info("Starting predictive analytics pipeline...")
        
        # Load and prepare data
        df = self.load_and_prepare_data()
        
        # Perform predictive analysis
        analysis = self.perform_predictive_analysis(df)
        
        # Create narratives
        narrative = self.create_predictive_narrative(analysis)
        dashboard = self.create_executive_dashboard(analysis)
        
        # Save reports
        narrative_path, dashboard_path = self.save_analysis(narrative, dashboard)
        
        logger.info("✅ Predictive analysis complete!")
        logger.info(f"📊 Upload these files to PrivateGPT:")
        logger.info(f"   1. {narrative_path}")
        logger.info(f"   2. {dashboard_path}")
        
        return narrative_path, dashboard_path, analysis

def main():
    """Main entry point."""
    csv_file = "Trend-Raw-Data_1.csv"
    
    if not Path(csv_file).exists():
        logger.error(f"CSV file not found: {csv_file}")
        return
    
    try:
        preprocessor = PredictiveAnalysisPreprocessor(csv_file)
        narrative_path, dashboard_path, analysis = preprocessor.process()
        
        print("\n" + "="*70)
        print("🎉 PREDICTIVE ANALYTICS COMPLETE!")
        print("="*70)
        print(f"📈 Predictive Analysis Report: {narrative_path}")
        print(f"📊 Executive Dashboard: {dashboard_path}")
        print(f"\n🎯 Device Risk Level: {analysis['risk_level']}")
        print(f"📊 Performance Score: {100 - analysis['risk_score']}/100")
        
        print("\n💡 Now you can ask PrivateGPT:")
        print("   • 'What is the predictive forecast for Device 3?'")
        print("   • 'Show me the risk assessment and maintenance recommendations'")
        print("   • 'What are the process capability metrics?'")
        print("   • 'Generate a maintenance schedule based on trends'")
        print("   • 'What is the executive summary of device performance?'")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()
