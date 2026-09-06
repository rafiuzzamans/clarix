import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def generate_confusion_matrices():
    report_path = 'c:/Project/ml/models/evaluation_report.json'
    out_dir = 'c:/Users/rafi/.gemini/antigravity-ide/brain/9aeae797-6d14-4041-92c0-b8620bbca1c3/scratch'
    
    os.makedirs(out_dir, exist_ok=True)
    
    with open(report_path, 'r') as f:
        data = json.load(f)
        
    for task in ['category', 'priority', 'sentiment']:
        cm = np.array(data[task]['confusion_matrix'])
        labels = data[task]['labels']
        
        plt.figure(figsize=(8, 6))
        
        # Normalize for color mapping, but display raw counts
        cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        ax = sns.heatmap(cm_norm, annot=cm, fmt='d', cmap='Blues', 
                         xticklabels=labels, yticklabels=labels, cbar=False,
                         annot_kws={"size": 12, "weight": "bold"})
                         
        plt.title(f'Figure 5.x: {task.capitalize()} Confusion Matrix', fontsize=14, pad=15, fontweight='bold', color='#2a4365')
        plt.ylabel('True Label', fontsize=12, fontweight='bold', color='gray')
        plt.xlabel('Predicted Label', fontsize=12, fontweight='bold', color='gray')
        
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        out_path = os.path.join(out_dir, f'cm_{task}.png')
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_confusion_matrices()
