# Documentation

This directory contains technical documentation for the PCC project.

## Model Analysis

**`model_analysis.ipynb`** - Comprehensive analysis of the Privacy Case Classifier model training process.

### Key Findings

- **ROC-AUC: 0.998** - Excellent class separability
- **PR-AUC: 0.998** - Outstanding performance on imbalanced dataset  
- **F1-Score: 0.97** - Balanced precision and recall
- **Accuracy: 97%** - High overall performance

### Analysis Components

1. **Data Validation** - Embedding vector validation and quality assessment
2. **Class Distribution** - Analysis of imbalanced dataset (544 NOT_PC, 214 PC)
3. **Data Balancing** - SMOTE application for 1:1 class balance
4. **Class Separability** - UMAP visualization showing clear class clusters
5. **Model Training** - Grid search optimization with cross-validation
6. **Performance Evaluation** - Comprehensive metrics and visualizations
7. **Model Persistence** - Model and metadata storage

### Technical Decisions

- **Algorithm:** LogisticRegression with L1 penalty (C=10)
- **Embeddings:** all-MiniLM-L6-v2 (384 dimensions)
- **Balancing:** SMOTE for minority class oversampling
- **Validation:** 5-fold cross-validation with F1 scoring
- **Split:** 80/20 train/test with stratification

### Model Characteristics

- **Purpose:** First-stage filter for privacy case identification
- **Focus:** High recall over precision for production use
- **Architecture:** Simple but effective linear classifier
- **Scalability:** Fast inference suitable for real-time processing

This analysis demonstrates that even a simple linear model achieves excellent performance when trained on high-quality embeddings, providing a solid foundation for the production pipeline. 
noteId: "ceb083705c5711f09e2863a97b2b4200"
tags: []

---

 