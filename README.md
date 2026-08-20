# Secure AI HR Agent: LLM03 - Excessive Agency

This repository demonstrates **Excessive Agency (LLM03)** in a real-world scenario: an AI-powered HR screening tool. It showcases how malicious actors can exploit Large Language Models (LLMs) that have unchecked access to critical system tools, and how to effectively mitigate this threat using a **Human-in-the-Loop (HITL) Gateway** and the **Honeypot Tool Pattern**.

---

## 🛑 The Vulnerability: Excessive Agency

In the vulnerable version of this application, an AI agent reads candidate resumes (PDFs) and is granted direct, unsupervised access to high-impact HR tools, such as `terminate_employee`[cite: 7].

An attacker can exploit this **Excessive Agency** by embedding hidden instructions (e.g., 1pt font size, white text) inside their submitted resume. When the backend PDF parser extracts this text, it is fed directly into the LLM[cite: 7]. Because the LLM is overly trusting and lacks an execution boundary, it treats the attacker's hidden payload as a legitimate command, invoking the tool and autonomously modifying the live HR database without any human verification[cite: 7].

## 🛡️ The Defense: Human-in-the-Loop & Honeypot Pattern

To secure the HR Agent, simply removing the tool entirely isn't always practical, and prompt engineering alone is insufficient. Instead, this project implements a strict execution boundary using two techniques:

1. **The Honeypot Tool Pattern:** The LLM is still provided a tool definition (e.g., `terminate_employee`) so it believes it has authorization[cite: 6]. This safely traps the prompt injection, forcing the LLM to format the malicious request as a predictable tool call rather than unpredictable text.
2. **Human-in-the-Loop (HITL) Gateway:** The actual security boundary is moved to the backend Python code. When the LLM attempts to invoke the dangerous tool, the execution layer intercepts the call, suspends the process, and requires explicit terminal input from a human administrator to authorize or block the action[cite: 6].

---

## 🌿 Agent Structure

This repository contains both the vulnerable and secure implementations side-by-side for educational purposes, accessible via a unified Web UI[cite: 2].

- **`vulnerable_agent.py`:** Contains the naive implementation where the LLM can directly execute database operations[cite: 7].
- **`secure_agent.py`:** Contains the secured code implementing the HITL gateway and Honeypot pattern[cite: 6].

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone [https://github.com/varkeymjohn/secure-AI-HR-agent.git](https://github.com/varkeymjohn/secure-AI-HR-agent.git)
cd secure-AI-HR-agent