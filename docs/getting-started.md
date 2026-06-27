# Getting Started

Welcome to GitAuditor! This guide will help you install and run GitAuditor for the first time.

## Installation

You can install GitAuditor from PyPI:

```bash
pip install gitauditor
```

Or from source:

```bash
git clone https://github.com/refernandes/gitauditor.git
cd gitauditor
pip install -e .
```

## First Run

Initialize your catalog database:

```bash
gitauditor catalog sync ~/projects/
```

Configure your AI provider:

```bash
gitauditor config set provider openai
gitauditor config set api_key sk-xxxx
```
