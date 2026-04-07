# 🧠 Notes Guide Agent – Multi-Agent AI Productivity System

## 📌 Overview
Notes Guide Agent is a multi-agent AI system designed to help users manage notes, tasks, and information through a single intelligent interface. It automates workflows like note-taking, task generation, and information retrieval using coordinated AI agents.

---

## 🚀 Features
- 🤖 Multi-Agent Architecture (Primary + Sub-agents)
- 📝 Notes Creation & Management
- ✅ Task Management System
- 🔄 Automated Task Extraction from Notes
- 🧠 AI-Powered Summarization (Gemini)
- 🔗 MCP Tool Integration
- 📂 Firebase Datastore Integration
- 🔐 IAM-Based Secure Access
- ⚡ FastAPI-based API System
- ☁️ Deployable on Cloud Run

---

## 🏗️ Architecture
- **Root Agent** – Handles user input and coordinates workflow  
- **Workspace Agent** – Executes tasks using tools  
- **Tools (via MCP)**:
  - Add Task  
  - List Tasks  
  - Complete Task  
  - Add Note  
- **Database** – Firebase Datastore (NoSQL)  
- **AI Engine** – Gemini API  

---

## 🔄 Workflow
1. User sends a request (e.g., create note)  
2. Root Agent processes input  
3. Request is delegated to Workspace Agent  
4. Tools are triggered via MCP  
5. Data is stored/retrieved from Datastore  
6. Gemini processes content (if required)  
7. Response is returned via API  

---

## 🛠️ Tech Stack
- Python  
- FastAPI  
- Google Agent Development Kit (ADK)  
- Gemini API  
- Firebase Datastore  
- MCP (Model Context Protocol)  
- Google Cloud Run  
- IAM (Identity & Access Management)  

---

## Snapshot

<img width="926" height="467" alt="image" src="https://github.com/user-attachments/assets/adbb1360-7730-4ba8-806a-9faa10fb5a4d" />
