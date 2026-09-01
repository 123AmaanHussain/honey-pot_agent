"""
System Evaluation Script
Measures accuracy, precision, recall, F1-score, FPR, FNR, and response time
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.detection import detect_scam, update_confidence
from app.core.agent import generate_reply


class SystemEvaluator:
    """Evaluates the honey-pot system performance metrics."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.results = {
            "true_positives": 0,
            "true_negatives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "response_times": [],
            "predictions": [],
            "errors": []
        }
        self.dataset = self._load_dataset()
    
    def _load_dataset(self) -> List[Dict]:
        """Load the evaluation dataset."""
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
        return data['test_messages']
    
    def evaluate_single_message(self, message_data: Dict) -> Tuple[bool, float]:
        """
        Evaluate a single message against the system.
        
        Returns:
            Tuple of (detected_as_scam, response_time)
        """
        message = message_data['message']
        actual_label = message_data['label']
        
        start_time = time.time()
        
        try:
            # Run scam detection
            result = detect_scam(message)
            detected = result['is_scam']
            confidence = result['confidence']
            flags = result['flags']
            
            # If scam detected, also test agent response generation
            if detected:
                try:
                    reply, persona, intel, should_exit = generate_reply(
                        confidence=confidence,
                        last_message=message,
                        message_history=[]
                    )
                except Exception as e:
                    self.results['errors'].append({
                        'message_id': message_data['id'],
                        'error': f"Agent generation failed: {str(e)}"
                    })
            
            response_time = time.time() - start_time
            
            return detected, response_time
            
        except Exception as e:
            self.results['errors'].append({
                'message_id': message_data['id'],
                'error': f"Detection failed: {str(e)}"
            })
            return False, time.time() - start_time
    
    def run_evaluation(self):
        """Run evaluation on all test messages."""
        print(f"📊 Starting evaluation on {len(self.dataset)} test messages...")
        print("=" * 60)
        
        for i, message_data in enumerate(self.dataset, 1):
            message_id = message_data['id']
            actual_label = message_data['label']
            expected_detection = message_data['expected_detection']
            
            print(f"[{i}/{len(self.dataset)}] Testing {message_id} ({actual_label})...")
            
            detected, response_time = self.evaluate_single_message(message_data)
            
            self.results['response_times'].append(response_time)
            
            # Record prediction
            self.results['predictions'].append({
                'id': message_id,
                'actual': actual_label,
                'predicted': 'scam' if detected else 'legitimate',
                'expected': 'scam' if expected_detection else 'legitimate',
                'response_time': response_time
            })
            
            # Calculate confusion matrix
            if actual_label == 'scam':
                if detected:
                    self.results['true_positives'] += 1
                    print(f"  ✅ Correctly detected as scam (TP)")
                else:
                    self.results['false_negatives'] += 1
                    print(f"  ❌ Failed to detect scam (FN)")
            else:  # legitimate
                if detected:
                    self.results['false_positives'] += 1
                    print(f"  ❌ False positive - legitimate flagged as scam (FP)")
                else:
                    self.results['true_negatives'] += 1
                    print(f"  ✅ Correctly passed through as legitimate (TN)")
        
        print("=" * 60)
        print("✅ Evaluation complete!")
    
    def calculate_metrics(self) -> Dict:
        """Calculate all performance metrics."""
        tp = self.results['true_positives']
        tn = self.results['true_negatives']
        fp = self.results['false_positives']
        fn = self.results['false_negatives']
        
        total = tp + tn + fp + fn
        total_actual_positives = tp + fn
        total_actual_negatives = tn + fp
        total_predicted_positives = tp + fp
        
        # Calculate metrics
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / total_predicted_positives if total_predicted_positives > 0 else 0
        recall = tp / total_actual_positives if total_actual_positives > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        false_positive_rate = fp / total_actual_negatives if total_actual_negatives > 0 else 0
        false_negative_rate = fn / total_actual_positives if total_actual_positives > 0 else 0
        
        # Response time metrics
        avg_response_time = sum(self.results['response_times']) / len(self.results['response_times'])
        min_response_time = min(self.results['response_times'])
        max_response_time = max(self.results['response_times'])
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'confusion_matrix': {
                'true_positives': tp,
                'true_negatives': tn,
                'false_positives': fp,
                'false_negatives': fn
            }
        }
    
    def generate_report(self):
        """Generate and display evaluation report."""
        metrics = self.calculate_metrics()
        
        print("\n" + "=" * 60)
        print("📊 SYSTEM EVALUATION REPORT")
        print("=" * 60)
        
        print("\n🎯 CLASSIFICATION METRICS")
        print("-" * 60)
        print(f"Accuracy:              {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"Precision:             {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
        print(f"Recall:                {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
        print(f"F1-Score:              {metrics['f1_score']:.4f} ({metrics['f1_score']*100:.2f}%)")
        print(f"False Positive Rate:   {metrics['false_positive_rate']:.4f} ({metrics['false_positive_rate']*100:.2f}%)")
        print(f"False Negative Rate:   {metrics['false_negative_rate']:.4f} ({metrics['false_negative_rate']*100:.2f}%)")
        
        print("\n⏱️  RESPONSE TIME METRICS")
        print("-" * 60)
        print(f"Average Response Time: {metrics['avg_response_time']:.4f}s")
        print(f"Min Response Time:     {metrics['min_response_time']:.4f}s")
        print(f"Max Response Time:     {metrics['max_response_time']:.4f}s")
        
        print("\n📊 CONFUSION MATRIX")
        print("-" * 60)
        cm = metrics['confusion_matrix']
        print(f"True Positives (TP):   {cm['true_positives']}")
        print(f"True Negatives (TN):   {cm['true_negatives']}")
        print(f"False Positives (FP):  {cm['false_positives']}")
        print(f"False Negatives (FN):  {cm['false_negatives']}")
        
        if self.results['errors']:
            print("\n⚠️  ERRORS")
            print("-" * 60)
            for error in self.results['errors']:
                print(f"  {error['message_id']}: {error['error']}")
        
        print("\n" + "=" * 60)
        
        # Save detailed results to JSON
        self._save_detailed_results(metrics)
        
        return metrics
    
    def _save_detailed_results(self, metrics: Dict):
        """Save detailed results to JSON file."""
        output = {
            'metrics': metrics,
            'predictions': self.results['predictions'],
            'errors': self.results['errors']
        }
        
        output_path = Path(__file__).parent / 'evaluation_results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"📁 Detailed results saved to: {output_path}")


def main():
    """Main evaluation function."""
    dataset_path = Path(__file__).parent / 'evaluation_dataset.json'
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found at: {dataset_path}")
        return
    
    evaluator = SystemEvaluator(str(dataset_path))
    evaluator.run_evaluation()
    metrics = evaluator.generate_report()
    
    print("\n✅ Evaluation complete!")
    return metrics


if __name__ == "__main__":
    main()
