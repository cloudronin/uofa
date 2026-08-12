---
license: apache-2.0
language:
- en
pipeline_tag: text-generation
base_model:
- allenai/OLMo-2-1124-13B-Instruct-RLVR2
library_name: transformers
datasets:
- allenai/RLVR-MATH
---

<img alt="OLMo Logo" src="https://huggingface.co/datasets/allenai/blog-images/resolve/main/olmo2/olmo.png" width="242px">

# OLMo-2-1124-13B-Instruct

## NOTE: 1/3/2025 UPDATE:

Upon the initial release of OLMo-2 models, we realized the post-trained models did not share the pre-tokenization logic that the base models use. As a result, we have trained new post-trained models. The new models are available under the same names as the original models, but we have made the old models available with a postfix "-preview". See [OLMo 2 Preview Post-trained Models](https://huggingface.co/collections/allenai/olmo-2-preview-post-trained-models-6762f662c660962e52de7c96) for the colleciton of the legacy models.

## Release Documentation

OLMo 2 13B Instruct November 2024 is post-trained variant of the [OLMo-2 13B November 2024](https://huggingface.co/allenai/OLMo2-13B-1124) model, which has undergone supervised finetuning on an OLMo-specific variant of the [Tülu 3 dataset](https://huggingface.co/datasets/allenai/tulu-3-sft-olmo-2-mixture and further DPO training on [this dataset](https://huggingface.co/datasets/allenai/olmo-2-1124-13b-preference-mix), and finally RLVR training using [this data](https://huggingface.co/datasets/allenai/RLVR-GSM).
Tülu 3 is designed for state-of-the-art performance on a diversity of tasks in addition to chat, such as MATH, GSM8K, and IFEval.
Check out the [OLMo 2 paper](https://arxiv.org/abs/2501.00656) or [Tülu 3 paper](https://arxiv.org/abs/2411.15124) for more details!

OLMo is a series of **O**pen **L**anguage **Mo**dels designed to enable the science of language models. 
These models are trained on the Dolma dataset. We are releasing all code, checkpoints, logs (coming soon), and associated training details. 
The core models released in this batch include the following:


| **Stage**           | **OLMo 2 7B**                                                                                          | **OLMo 2 13B**                                                                                         |
|----------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Base Model**       | [allenai/OLMo2-7B-1124](https://huggingface.co/allenai/OLMo2-7B-1124)                                | [allenai/OLMo-2-13B-1124](https://huggingface.co/allenai/OLMo-2-13B-1124)                             |
| **SFT**              | [allenai/OLMo-2-1124-7B-SFT](https://huggingface.co/allenai/OLMo-2-1124-7B-SFT)                | [allenai/OLMo-2-1124-13B-SFT](https://huggingface.co/allenai/OLMo-2-1124-13B-SFT)              |
| **DPO**              | [allenai/OLMo-2-1124-7B-DPO](https://huggingface.co/allenai/OLMo-2-1124-7B-DPO)                | [allenai/OLMo-2-1124-13B-DPO](https://huggingface.co/allenai/OLMo-2-1124-13B-DPO)              |
| **Final Models (RLVR)** | [allenai/OLMo-2-1124-7B-Instruct](https://huggingface.co/allenai/OLMo-2-1124-7B-Instruct)                        | [allenai/OLMo-2-1124-13B-Instruct](https://huggingface.co/allenai/OLMo-2-1124-13B-Instruct)                      |
| **Reward Model (RM)**| [allenai/OLMo-2-1124-7B-RM](https://huggingface.co/allenai/OLMo-2-1124-7B-RM)                                                     | [allenai/OLMo-2-1124-13B-RM](https://huggingface.co/allenai/OLMo-2-1124-13B-RM)                                                     |



## Model description

- **Model type:** A model trained on a mix of publicly available, synthetic and human-created datasets.
- **Language(s) (NLP):** Primarily English
- **License:** Apache 2.0
- **Finetuned from model:** allenai/OLMo-2-13B-1124-RLVR2

### Model Sources

- **Project Page:** https://allenai.org/olmo
- **Repositories:** 
    - Core repo (training, inference, fine-tuning etc.): https://github.com/allenai/OLMo
    - Evaluation code: https://github.com/allenai/olmes
    - Further fine-tuning code: https://github.com/allenai/open-instruct
- **Paper:** https://arxiv.org/abs/2501.00656
- **Demo:** https://playground.allenai.org/

## Installation

OLMo 2 will be supported in the next version of Transformers, and you need to install it from the main branch using:
```bash
pip install --upgrade git+https://github.com/huggingface/transformers.git
```

## Using the model

### Loading with HuggingFace

To load the model with HuggingFace, use the following snippet:
```
from transformers import AutoModelForCausalLM

olmo_model = AutoModelForCausalLM.from_pretrained("allenai/OLMo-2-1124-13B-Instruct")
```

### Chat template

The chat template for our models is formatted as:
```
<|endoftext|><|user|>\nHow are you doing?\n<|assistant|>\nI'm just a computer program, so I don't have feelings, but I'm functioning as expected. How can I assist you today?<|endoftext|>
```
Or with new lines expanded:
```
<|endoftext|><|user|>
How are you doing?
<|assistant|>
I'm just a computer program, so I don't have feelings, but I'm functioning as expected. How can I assist you today?<|endoftext|>
```
It is embedded within the tokenizer as well, for `tokenizer.apply_chat_template`.

### System prompt

In Ai2 demos, we use this system prompt by default:
```
You are OLMo 2, a helpful and harmless AI Assistant built by the Allen Institute for AI.
```
The model has not been trained with a specific system prompt in mind.

### Bias, Risks, and Limitations

The OLMo-2 models have limited safety training, but are not deployed automatically with in-the-loop filtering of responses like ChatGPT, so the model can produce problematic outputs (especially when prompted to do so). 
See the Falcon 180B model card for an example of this.


## Performance

| Model | Average | AlpacaEval | BBH | DROP | GSM8k | IFEval | MATH | MMLU | Safety | PopQA | TruthQA |
|-------|---------|------------|-----|------|--------|---------|------|-------|---------|-------|---------|
| **Open weights models** |
| Gemma-2-9B-it | 51.9 | 43.7 | 2.5 | 58.8 | 79.7 | 69.9 | 29.8 | 69.1 | 75.5 | 28.3 | 61.4 |
| Ministral-8B-Instruct | 52.1 | 31.4 | 56.2 | 56.2 | 80.0 | 56.4 | 40.0 | 68.5 | 56.2 | 20.2 | 55.5 |
| Mistral-Nemo-Instruct-2407 | 50.9 | 45.8 | 54.6 | 23.6 | 81.4 | 64.5 | 31.9 | 70.0 | 52.7 | 26.9 | 57.7 |
| Qwen-2.5-7B-Instruct | 57.1 | 29.7 | 25.3 | 54.4 | 83.8 | 74.7 | 69.9 | 76.6 | 75.0 | 18.1 | 63.1 |
| Llama-3.1-8B-Instruct | 58.9 | 25.8 | 69.7 | 61.7 | 83.4 | 80.6 | 42.5 | 71.3 | 70.2 | 28.4 | 55.1 |
| Tülu 3 8B | 60.4 | 34.0 | 66.0 | 62.6 | 87.6 | 82.4 | 43.7 | 68.2 | 75.4 | 29.1 | 55.0 |
| Qwen-2.5-14B-Instruct | 60.8 | 34.6 | 34.0 | 50.5 | 83.9 | 82.4 | 70.6 | 81.1 | 79.3 | 21.1 | 70.8 |
| **Fully open models** |
| OLMo-7B-Instruct | 28.2 | 5.2 | 35.3 | 30.7 | 14.3 | 32.2 | 2.1 | 46.3 | 54.0 | 17.1 | 44.5 |
| OLMo-7B-0424-Instruct | 33.1 | 8.5 | 34.4 | 47.9 | 23.2 | 39.2 | 5.2 | 48.9 | 49.3 | 18.9 | 55.2 |
| OLMoE-1B-7B-0924-Instruct | 35.5 | 8.5 | 37.2 | 34.3 | 47.2 | 46.2 | 8.4 | 51.6 | 51.6 | 20.6 | 49.1 |
| MAP-Neo-7B-Instruct | 42.9 | 17.6 | 26.4 | 48.2 | 69.4 | 35.9 | 31.5 | 56.5 | 73.7 | 18.4 | 51.6 |
| *OLMo-2-7B-SFT* | 50.2 | 10.2 | 49.7 | 59.6 | 74.6 | 66.9 | 25.3 | 61.1 | 82.1 | 23.6 | 48.6 |
| *OLMo-2-7B-DPO* | 54.2 | 27.9 | 46.7 | 60.2 | 82.6 | 73.0 | 30.3 | 60.8 | 81.0 | 23.5 | 56.0 |
| *OLMo-2-13B-SFT* | 55.3 | 11.5 | 59.6 | 71.3 | 76.3 | 68.6 | 29.5 | 68.0 | 82.3 | 29.4 | 57.1 |
| *OLMo-2-13B-DPO* | 60.6 | 38.3 | 57.9 | 71.5 | 82.3 | 80.2 | 35.2 | 67.9 | 79.7 | 29.0 | 63.9 |
| **OLMo-2-7B-1124–Instruct** | 54.8 | 29.1 | 46.6 | 60.5 | 85.1 | 72.3 | 32.5 | 61.3 | 80.6 | 23.2 | 56.5 |
| **OLMo-2-13B-1124-Instruct** | 62.0 | 39.5 | 58.8 | 71.5 | 87.4 | 82.6 | 39.2 | 68.5 | 79.1 | 28.8 | 64.3 |


## License and use

OLMo 2 is licensed under the Apache 2.0 license.
OLMo 2 is intended for research and educational use.
For more information, please see our [Responsible Use Guidelines](https://allenai.org/responsible-use).
This model has been fine-tuned using a dataset mix with outputs generated from third party models and are subject to additional terms: [Gemma Terms of Use](https://ai.google.dev/gemma/terms).

## Citation

```bibtex
@article{olmo20242olmo2furious,
      title={2 OLMo 2 Furious}, 
      author={Team OLMo and Pete Walsh and Luca Soldaini and Dirk Groeneveld and Kyle Lo and Shane Arora and Akshita Bhagia and Yuling Gu and Shengyi Huang and Matt Jordan and Nathan Lambert and Dustin Schwenk and Oyvind Tafjord and Taira Anderson and David Atkinson and Faeze Brahman and Christopher Clark and Pradeep Dasigi and Nouha Dziri and Michal Guerquin and Hamish Ivison and Pang Wei Koh and Jiacheng Liu and Saumya Malik and William Merrill and Lester James V. Miranda and Jacob Morrison and Tyler Murray and Crystal Nam and Valentina Pyatkin and Aman Rangapur and Michael Schmitz and Sam Skjonsberg and David Wadden and Christopher Wilhelm and Michael Wilson and Luke Zettlemoyer and Ali Farhadi and Noah A. Smith and Hannaneh Hajishirzi},
      year={2024},
      eprint={2501.00656},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2501.00656}, 
}
```

