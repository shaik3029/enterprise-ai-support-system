from langchain_groq import ChatGroq
import os

from backend.rag_engine import query_rag
from database.db_manager import get_user_details, create_ticket

# ============================================================
# GROQ LLM INITIALIZATION
# ============================================================

def get_llm(api_key: str):
    return ChatGroq(
        groq_api_key=api_key,
        model_name="openai/gpt-oss-20b",
        temperature=0.2
    )

# ============================================================
# MULTI-AGENT ORCHESTRATOR
# ============================================================

def handle_user_query(
    user_id: str,
    query: str,
    groq_api_key: str
) -> dict:
    if not groq_api_key:
        return {
            "agent": "System",
            "response": "Groq API key is missing or not configured in environment."
        }

    llm = get_llm(groq_api_key)
    query_lower = query.lower().strip()

    # ========================================================
    # CLARIFICATION AGENT — AMBIGUOUS CUSTOMER QUESTIONS
    # ========================================================
    ambiguous_account_phrases = [
        "why is my account not working",
        "why my account is not working",
        "account not working",
        "my account isn't working",
        "my account is not working",
        "account doesn't work",
        "account does not work"
    ]

    if any(phrase in query_lower for phrase in ambiguous_account_phrases):
        return {
            "agent": "Clarification Agent",
            "response": (
                "I can certainly help you troubleshoot that. To assist you accurately, "
                "could you clarify which service or feature you are trying to access "
                "(for example: portal sign-in, billing/subscription, API key, or profile settings)?"
            )
        }

    # ========================================================
    # AGENT 1 — DATABASE / ACCOUNT AGENT
    # ========================================================
    account_keywords = [
        "balance",
        "plan",
        "status",
        "my account",
        "subscription",
        "profile",
        "tier",
        "billing",
        "invoice"
    ]

    if any(keyword in query_lower for keyword in account_keywords):
        user_info = get_user_details(user_id)
        if user_info:
            name = user_info.get("name", "Valued Customer")
            plan = user_info.get("plan", "Standard Plan")
            balance = user_info.get("account_balance", "$0.00")
            status = user_info.get("status", "Active")

            prompt = f"""
You are an enterprise customer support assistant.

CUSTOMER INFORMATION:
Name: {name}
Plan: {plan}
Account Balance: {balance}
Account Status: {status}

CUSTOMER QUESTION:
{query}

Instructions:
- Use the customer information exactly as provided.
- Do not invent account numbers or hypothetical balances.
- Give a courteous, concise, and professional enterprise support response.
"""
            try:
                response = llm.invoke(prompt)
                return {
                    "agent": "Database Agent",
                    "response": response.content.strip()
                }
            except Exception as e:
                return {
                    "agent": "Database Agent",
                    "response": f"Your account status is currently **{status}** with plan **{plan}** and balance **{balance}**."
                }
        else:
            return {
                "agent": "Database Agent",
                "response": f"User record for '{user_id}' was not found in the enterprise database."
            }

    # ========================================================
    # AGENT 2 — KNOWLEDGE BASE / RAG POLICY AGENT
    # ========================================================
    policy_keywords = [
        "policy",
        "refund",
        "sla",
        "password",
        "charge",
        "fee",
        "mfa",
        "security",
        "authentication",
        "access control",
        "privacy",
        "compliance",
        "zero trust",
        "risk",
        "incident",
        "encryption",
        "nist",
        "disaster recovery"
    ]

    if any(keyword in query_lower for keyword in policy_keywords):
        context_chunks = query_rag(query)
        if not context_chunks:
            return {
                "agent": "RAG Policy Agent",
                "response": (
                    "I searched the Enterprise Knowledge Base and policy documentation, "
                    "but could not find specific guidance answering this query. "
                    "Would you like me to open a support ticket for a specialist to assist you?"
                )
            }

        context = "\n\n--- DOCUMENT SECTION ---\n\n".join(context_chunks)
        prompt = f"""
You are the Enterprise Knowledge Base Support Agent.
Answer the user's question using ONLY the official knowledge base context below.

==============================
OFFICIAL ENTERPRISE KNOWLEDGE BASE
==============================
{context}

==============================
USER QUESTION
==============================
{query}

==============================
ANSWERING RULES
==============================
1. Use only information verified in the knowledge base.
2. Do not invent policies, dates, figures, or compliance regulations.
3. If the knowledge base does not contain enough information, state:
   "The official knowledge base does not contain sufficient details to address this question completely. Please contact human support."
4. Provide a well-structured, clear, and professional answer.
"""
        try:
            response = llm.invoke(prompt)
            return {
                "agent": "RAG Policy Agent",
                "response": response.content.strip() if response.content else "Information retrieved from policy documentation."
            }
        except Exception as e:
            return {
                "agent": "RAG Policy Agent",
                "response": "According to the enterprise security and compliance documentation: " + context_chunks[0][:300] + "..."
            }

    # ========================================================
    # AGENT 3 — TICKETING / HUMAN ESCALATION AGENT
    # ========================================================
    escalation_keywords = [
        "ticket",
        "human",
        "agent",
        "complaint",
        "escalate",
        "issue",
        "broken",
        "bug",
        "problem",
        "frustrated",
        "speak to a person"
    ]

    if any(keyword in query_lower for keyword in escalation_keywords):
        try:
            ticket_id = create_ticket(user_id=user_id, issue_description=query, priority="MEDIUM")
            prompt = f"""
You are an enterprise customer support assistant.
A support ticket has been created with ID #{ticket_id} for User ID '{user_id}'.
Customer Issue: {query}

Write a short, empathetic, professional response informing the customer that ticket #{ticket_id} has been created and assigned to the support engineering team.
"""
            response = llm.invoke(prompt)
            return {
                "agent": "Ticketing Agent",
                "response": response.content.strip()
            }
        except Exception as e:
            return {
                "agent": "Ticketing Agent",
                "response": f"Your issue has been recorded and escalated to human support. A support engineer will review it promptly."
            }

    # ========================================================
    # AGENT 4 — GENERAL SUPPORT AGENT (FALLBACK)
    # ========================================================
    prompt = f"""
You are an enterprise customer support assistant for SupportAI.
Customer question:
{query}

Provide a polite, professional, and helpful response.
Do not invent customer private data or unverified policies.
"""
    try:
        response = llm.invoke(prompt)
        return {
            "agent": "General Support Agent",
            "response": response.content.strip()
        }
    except Exception as e:
        return {
            "agent": "General Support Agent",
            "response": "Hello! I am your Enterprise AI Assistant. How can I assist you with your account, security policies, or support tickets today?"
        }