import json
import matplotlib.pyplot as plt
import numpy as np

def generate_figure():
    # Load data
    with open('c:/Project/ml/models/evaluation_report.json', 'r') as f:
        data = json.load(f)

    cat_f1 = data['category']['per_class_f1']
    pri_f1 = data['priority']['per_class_f1']
    sent_f1 = data['sentiment']['per_class_f1']
    
    # Sort category F1 descending
    cat_sorted = sorted(cat_f1.items(), key=lambda x: x[1], reverse=False) # Reverse False so highest is at top when plotted
    
    # Structure data for plotting (from bottom to top)
    labels = []
    values = []
    colors = []
    
    # Colors
    c_blue = '#2360a0'
    c_green = '#156a4e'
    c_brown = '#8a4b16'
    c_purple = '#5d47ab'
    c_red = '#ee4c3d'
    
    # Sentiment
    sent_sorted = sorted(sent_f1.items(), key=lambda x: x[1], reverse=False) # negative, positive, neutral (neutral highest)
    labels.extend(['negative', 'positive', 'neutral'])
    values.extend([sent_f1['negative'], sent_f1['positive'], sent_f1['neutral']])
    colors.extend([c_red, c_red, c_green])
    
    # Priority
    labels.extend(['medium', 'low', 'high'])
    values.extend([pri_f1['medium'], pri_f1['low'], pri_f1['high']])
    colors.extend([c_purple, c_purple, c_purple])
    
    # Category
    labels.extend([k for k, v in cat_sorted])
    values.extend([v for k, v in cat_sorted])
    
    for i in range(len(cat_sorted)):
        if i == 0:
            colors.append(c_brown) # lowest category
        elif i >= len(cat_sorted) - 3:
            colors.append(c_blue) # top 3 category
        else:
            colors.append(c_green)
            
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    y_pos = np.arange(len(labels))
    
    # Add gaps between groups
    y_pos[3:6] += 1
    y_pos[6:] += 2
    
    bars = ax.barh(y_pos, values, color=colors, height=0.7)
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        text = f"{width:.3f}"
        if labels[i] == 'mortgage':
            text += ' \u25A1' # small square symbol
        elif labels[i] == 'debt_collection':
            text += ' \u25BC' # down triangle
        elif labels[i] in ['negative', 'positive']:
            text += ' \u25A1'
            color = c_red
        else:
            color = colors[i]
            
        ax.text(width + 0.01, bar.get_y() + bar.get_height()/2, text, 
                ha='left', va='center', fontweight='bold', color=colors[i], fontsize=10)

    # Threshold line
    ax.axvline(x=0.7, color=c_red, linestyle='--', linewidth=1, zorder=0)
    ax.text(0.7, -1, "0.70 min", color=c_red, fontweight='bold', ha='center', va='top', fontsize=9)
    
    # Group separators
    ax.axhline(y=y_pos[3]-1, color='lightgray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(y=y_pos[6]-1, color='lightgray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 1.1)
    
    # Hide spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.xaxis.set_visible(False)
    
    # Group labels
    ax.text(-0.02, y_pos[4], "Priority", ha='right', va='center', color='gray', style='italic', fontsize=9)
    ax.text(-0.02, y_pos[2], "Sentiment", ha='right', va='center', color='gray', style='italic', fontsize=9)
    
    # Title
    plt.title("Figure 5.1: Per-Class F1-Score \u2014 Logistic Regression (Production Model)", 
              color='#2a4365', fontweight='bold', fontsize=13, pad=20)
              
    # Legend
    import matplotlib.patches as mpatches
    leg1 = mpatches.Patch(color=c_blue, label='Category (high)')
    leg2 = mpatches.Patch(color=c_brown, label='Category lowest')
    leg3 = mpatches.Patch(color=c_purple, label='Priority')
    leg4 = mpatches.Patch(color=c_red, label='Sentiment below 0.70 \u25A1')
    
    fig.legend(handles=[leg1, leg2, leg3, leg4], loc='lower center', bbox_to_anchor=(0.5, 0.12),
               ncol=4, frameon=False, handlelength=1.5, fontsize=9)
               
    # Footer text
    fig.text(0.5, 0.08, "Cat F1=0.881 \u00B7 Pri F1=0.869 \u00B7 Sent F1=0.733 (weighted avg) \u00B7   =highest \u00B7 \u25BC=lowest", 
             ha='center', fontsize=9, color='gray', style='italic')
    fig.text(0.5, 0.05, "Sentiment per-class below 0.70 \u2014 FinancialPhraseBank investor domain vs consumer complaint domain", 
             ha='center', fontsize=9, color=c_red, style='italic')
             
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2, left=0.2)
    
    plt.savefig('C:/Users/rafi/.gemini/antigravity-ide/brain/9aeae797-6d14-4041-92c0-b8620bbca1c3/scratch/figure_5_1.png', dpi=300, bbox_inches='tight')
    print("Successfully generated C:/Users/rafi/.gemini/antigravity-ide/brain/9aeae797-6d14-4041-92c0-b8620bbca1c3/scratch/figure_5_1.png")

if __name__ == "__main__":
    generate_figure()
