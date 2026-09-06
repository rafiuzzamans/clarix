import matplotlib.pyplot as plt
import numpy as np
import os

def generate_comparative_chart():
    out_dir = 'c:/Users/rafi/.gemini/antigravity-ide/brain/9aeae797-6d14-4041-92c0-b8620bbca1c3/scratch'
    os.makedirs(out_dir, exist_ok=True)

    # Data from Table 2.2 in the report
    models = ['Logistic Regression\n(Production)', 'LinearSVC\n(Calibrated)', 'Random Forest', 'Naive Bayes']
    
    cat_f1 = [0.881, 0.865, 0.803, 0.793]
    pri_f1 = [0.869, 0.809, 0.768, 0.612]
    sent_f1 = [0.733, 0.718, 0.697, 0.655]

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    rects1 = ax.bar(x - width, cat_f1, width, label='Category F1', color='#1f609e')
    rects2 = ax.bar(x, pri_f1, width, label='Priority F1', color='#5949b2')
    rects3 = ax.bar(x + width, sent_f1, width, label='Sentiment F1', color='#1c735a')

    # Threshold line
    ax.axhline(y=0.70, color='#ef5343', linestyle='--', linewidth=1.5, zorder=0)
    ax.text(len(models)-0.5, 0.705, "0.70 min threshold", color='#ef5343', fontweight='bold', ha='right', va='bottom')

    # Formatting
    ax.set_ylabel('Weighted F1-Score', fontsize=12, fontweight='bold', color='gray')
    ax.set_title('Figure 5.x: CLARIX vs Alternative Models (Comparative F1)', fontsize=14, fontweight='bold', color='#2a4365', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontweight='bold', color='#333333')
    ax.set_ylim(0.5, 1.0) # Zoom in on the relevant range

    # Legend
    ax.legend(loc='upper right', frameon=True, fontsize=10)
    
    # Hide top/right spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Annotate bars with values
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, rotation=0)

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    plt.tight_layout()
    out_path = os.path.join(out_dir, 'comparative_f1.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_comparative_chart()
