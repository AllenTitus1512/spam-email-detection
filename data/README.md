# AVN Phishing Email Classification Dataset

### Created by AVN Bluefox
### Published under **AVN Innovations**

## Overview

This project brings together two related email datasets designed for exploring how machine-learning models distinguish between legitimate and phishing messages.
The collection also includes a small amount of intentionally noisy data to resemble real-world imperfections and to allow learners to practice preprocessing techniques.

The goal is to offer a resource that is useful for students, researchers, and anyone interested in NLP, text classification, or cybersecurity.

## Included Files

### AVN_Basic.csv

This file contains 60,000 emails that have been cleaned and organized into a consistent structure.
Each email includes:

subject
sender
receiver
body text
number of URLs found
date
label 

#### Label meanings

0 — Legitimate
1 — Phishing
2 — Garbage / intentionally added noise

The “garbage” class represents noisy or unusable messages that were included on purpose.
It allows learners to practice tasks such as:

data cleaning
handling inconsistent labels
filtering irrelevant samples
building models that remain stable even when the dataset is imperfect

#### Class Counts

Legitimate: 31,122
Phishing: 28,476
Garbage: 402

This dataset is ideal for anyone who wants to work on multiclass classification or model robustness.

### AVN_Corpus.csv (Clean Version)

This file provides a simpler, cleaner dataset containing only legitimate and phishing emails.
It does not include garbage or intentionally noisy labels.

#### Label meanings

0 — Legitimate
1 — Phishing

It is especially useful for:

training baseline models
comparing performance between clean and noisy datasets
studying email patterns without distractions
teaching supervised learning without focusing on data cleanup
This file serves as the binary reference dataset, while AVN_Basic.csv represents the realistic, noisy version.

Working with both gives learners a chance to explore:

how noise affects accuracy
when models fail or improve
how preprocessing changes outcomes
how binary and multiclass tasks differ

### Purpose of the Dataset

This dataset was created to support learning and experimentation in:

phishing detection
spam classification
cybersecurity analytics
natural-language processing
text-based machine-learning projects

By providing both a clean corpus and a more realistic noisy corpus, the dataset encourages exploration at different skill levels—beginner to advanced.

## License

This dataset is released under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
This means you may share, adapt, and build upon the dataset for any purpose, even commercially, as long as you provide proper attribution to **AVN Bluefox**.

## Author

AVN Bluefox
Cybersecurity & AI Enthusiast
Published under **AVN Innovations**