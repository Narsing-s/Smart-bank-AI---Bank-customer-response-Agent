"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ArrowDownLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bot, Check, ChevronDown,
  CircleHelp, Clock3, CreditCard, Headphones, Landmark, LockKeyhole, MessageCircle,
  Plus, Send, ShieldCheck, Sparkles, WalletCards, X
} from "lucide-react";

type Language = "en" | "te" | "hi";
type ChatMessage = { id: string; role: "assistant" | "user"; text: string; time: string; intent?: string };
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

const copy = {
  en: {
    greeting: "Hello! How can I help you today?",
    intro: "I can help with everyday banking questions, card safety, and transaction guidance.",
    placeholder: "Ask me anything about banking…",
    welcome: "Your banking, made simpler.",
    sub: "A little help goes a long way. Ask a question or choose a quick action.",
    quick: "Quick actions",
    recent: "Helpful topics",
    security: "Your safety comes first",
    securityText: "Never share your PIN, password, CVV, or OTP with anyone.",
    support: "Need a human?",
    supportText: "For urgent or account-specific requests, use your bank’s official support channel.",
    send: "Send message",
    demo: "DEMO ENVIRONMENT",
    online: "Assistant online",
    suggestions: ["How do I block a lost card?", "My transaction failed", "Get an account statement", "UPI safety tips"],
    topics: ["Cards & PIN", "Failed transactions", "Account statements", "UPI safety"],
    footer: "SmartBank AI is a demonstration, not a real bank service.",
  },
  te: {
    greeting: "నమస్కారం! ఈ రోజు నేను మీకు ఎలా సహాయపడగలను?",
    intro: "సాధారణ బ్యాంకింగ్ ప్రశ్నలు, కార్డ్ భద్రత, లావాదేవీల గురించి సహాయం పొందండి.",
    placeholder: "బ్యాంకింగ్ గురించి అడగండి…",
    welcome: "మీ బ్యాంకింగ్ మరింత సులభం.",
    sub: "మీ ప్రశ్న అడగండి లేదా త్వరిత చర్యను ఎంచుకోండి.",
    quick: "త్వరిత చర్యలు",
    recent: "సహాయక అంశాలు",
    security: "మీ భద్రతే ముఖ్యం",
    securityText: "మీ PIN, పాస్‌వర్డ్, CVV లేదా OTP ఎవరికీ చెప్పవద్దు.",
    support: "మనిషితో మాట్లాడాలా?",
    supportText: "అత్యవసర విషయాలకు మీ బ్యాంక్ అధికారిక సహాయ మార్గాన్ని ఉపయోగించండి.",
    send: "పంపండి",
    demo: "డెమో వాతావరణం",
    online: "సహాయకుడు అందుబాటులో ఉన్నాడు",
    suggestions: ["పోయిన కార్డును ఎలా బ్లాక్ చేయాలి?", "నా లావాదేవీ విఫలమైంది", "ఖాతా స్టేట్‌మెంట్ పొందాలి", "UPI భద్రత"],
    topics: ["కార్డులు & PIN", "విఫలమైన లావాదేవీలు", "ఖాతా స్టేట్‌మెంట్‌లు", "UPI భద్రత"],
    footer: "SmartBank AI ఒక డెమో మాత్రమే; ఇది నిజమైన బ్యాంక్ సేవ కాదు.",
  },
  hi: {
    greeting: "नमस्ते! आज मैं आपकी कैसे मदद कर सकता हूँ?",
    intro: "रोज़मर्रा के बैंकिंग सवालों, कार्ड सुरक्षा और लेन-देन की जानकारी में मदद लें।",
    placeholder: "बैंकिंग के बारे में पूछें…",
    welcome: "आपकी बैंकिंग, और आसान।",
    sub: "अपना सवाल पूछें या कोई त्वरित विकल्प चुनें।",
    quick: "त्वरित विकल्प",
    recent: "मददगार विषय",
    security: "आपकी सुरक्षा सबसे पहले",
    securityText: "अपना PIN, पासवर्ड, CVV या OTP किसी से साझा न करें।",
    support: "किसी प्रतिनिधि से बात करें?",
    supportText: "ज़रूरी या खाते से जुड़े मामलों में बैंक के आधिकारिक सहायता चैनल का उपयोग करें।",
    send: "संदेश भेजें",
    demo: "डेमो वातावरण",
    online: "सहायक ऑनलाइन है",
    suggestions: ["खोया हुआ कार्ड कैसे ब्लॉक करें?", "मेरा लेन-देन विफल हुआ", "खाते का विवरण पाएँ", "UPI सुरक्षा सुझाव"],
    topics: ["कार्ड और PIN", "विफल लेन-देन", "खाते का विवरण", "UPI सुरक्षा"],
    footer: "SmartBank AI केवल एक डेमो है, वास्तविक बैंक सेवा नहीं।",
  },
} as const;

const actionItems = [
  { icon: CreditCard, title: "Card & PIN help", question: "How can I reset my debit card PIN?", tone: "blue" },
  { icon: ArrowDownLeft, title: "Failed transaction", question: "What should I do if my transaction failed?", tone: "violet" },
  { icon: WalletCards, title: "Account statement", question: "How can I get my account statement?", tone: "green" },
  { icon: ShieldCheck, title: "UPI safety", question: "How do I stay safe with UPI?", tone: "amber" },
];

function clock() {
  return new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit" }).format(new Date());
}

export default function Home() {
  const [language, setLanguage] = useState<Language>("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [caseOpen, setCaseOpen] = useState(false);
  const [caseCategory, setCaseCategory] = useState("service");
  const [caseDescription, setCaseDescription] = useState("");
  const [caseResult, setCaseResult] = useState("");
  const [caseId, setCaseId] = useState("");
  const [caseTrackingResult, setCaseTrackingResult] = useState("");
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  const endRef = useRef<HTMLDivElement>(null);
  const t = copy[language];

  useEffect(() => {
    fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2500) })
      .then((r) => { if (!r.ok) throw new Error("offline"); return r.json(); })
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);

  function startChat(question?: string) {
    setChatOpen(true);
    if (messages.length === 0) {
      setMessages([{ id: crypto.randomUUID(), role: "assistant", text: `${t.greeting}\n\n${t.intro}`, time: clock() }]);
    }
    if (question) void sendMessage(question);
  }

  async function sendMessage(text = input) {
    const message = text.trim();
    if (!message || busy) return;
    setChatOpen(true);
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", text: message, time: clock() };
    const current = messages.length === 0
      ? [{ id: crypto.randomUUID(), role: "assistant" as const, text: `${t.greeting}\n\n${t.intro}`, time: clock() }]
      : [];
    setMessages((prev) => [...prev, ...current, userMessage]);
    setInput("");
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, language }),
        signal: AbortSignal.timeout(8000),
      });
      if (!response.ok) throw new Error("API unavailable");
      const data = await response.json();
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", text: data.answer, time: clock(), intent: data.intent }]);
    } catch {
      const lower = message.toLowerCase();
      let answer = "I can help with common banking questions, but the demo API is currently unavailable. Please start the backend or try again later. For urgent matters, use your bank’s official support channel.";
      if (lower.includes("pin") || lower.includes("otp") || lower.includes("password") || lower.includes("cvv")) {
        answer = "For your safety, never share a PIN, password, CVV, or OTP in chat. Use only your bank’s official app, website, ATM, or verified customer-care channel.";
      } else if (lower.includes("lost card") || lower.includes("block card")) {
        answer = "If your card is lost or stolen, block it immediately through your bank’s official app, internet banking, or verified customer-care channel. Review recent transactions.";
      } else if (lower.includes("failed") || lower.includes("deducted")) {
        answer = "Check the status in your bank’s official app and save the reference number. If money was debited but the recipient was not credited, raise a complaint through the official channel.";
      }
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", text: answer, time: clock() }]);
    } finally {
      setBusy(false);
    }
  }

  async function submitCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCaseResult("");
    setCaseTrackingResult("");
    setCaseId("");
    try {
      const response = await fetch(`${API_BASE}/api/complaints`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: caseCategory, description: caseDescription }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to create demo case");
      setCaseId(data.case_id);
      setCaseResult(`Case ${data.case_id} received. Demo only — not sent to a real bank.`);
      setCaseDescription("");
    } catch {
      setCaseResult("The demo API is unavailable. Please start the backend and try again.");
    }
  }

  async function trackDemoCase() {
    if (!caseId) return;
    setCaseTrackingResult("Checking demo case status…");
    try {
      const response = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(caseId)}`, {
        signal: AbortSignal.timeout(5000),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to find demo case");
      setCaseTrackingResult(`Status: ${data.status} · Created: ${new Date(data.created_at).toLocaleString()} · Demo only.`);
    } catch {
      setCaseTrackingResult("Unable to check this demo case right now. Please try again.");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="SmartBank AI home">
          <span className="brand-mark"><Landmark size={23} strokeWidth={2.2} /></span>
          <span className="brand-copy"><strong>smartbank<span>AI</span></strong><small>CARE THAT CONNECTS</small></span>
        </a>
        <div className="top-actions">
          <span className="demo-pill"><span className="demo-dot" />{t.demo}</span>
          <label className="language-select"><span className="sr-only">Choose language</span><select value={language} onChange={(e) => setLanguage(e.target.value as Language)}><option value="en">EN · English</option><option value="te">TE · తెలుగు</option><option value="hi">HI · हिन्दी</option></select><ChevronDown size={14} /></label>
          <button className="avatar" onClick={() => setCaseOpen(true)} aria-label="Open support case">S</button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-content">
          <div className="eyebrow"><Sparkles size={14} /> YOUR PERSONAL BANKING ASSISTANT</div>
          <h1>{t.welcome.split(",")[0]}<br /><span>{t.welcome.includes(",") ? t.welcome.slice(t.welcome.indexOf(",") + 1).trim() : ""}</span></h1>
          <p>{t.sub}</p>
          <div className="hero-status"><span className={apiStatus === "online" ? "status-dot" : "status-dot status-warn"} />{apiStatus === "online" ? t.online : apiStatus === "checking" ? "Checking demo service…" : "Guided demo mode"}<span className="status-divider" /><ShieldCheck size={15} /> Security-first by design</div>
          <div className="hero-cta">
            <button className="primary-button" onClick={() => startChat()}><MessageCircle size={17} /> Chat with SmartBank <ArrowRight size={16} /></button>
            <button className="text-button" onClick={() => setCaseOpen(true)}><Headphones size={17} /> Create support case</button>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <div className="art-card">
            <div className="art-card-top"><span className="mini-bank"><Landmark size={18} /></span><span className="verified"><BadgeCheck size={15} /> Verified guidance</span></div>
            <div className="art-bubble"><span className="bot-orb"><Bot size={26} /></span><span><strong>How can I help?</strong><small>Here for your everyday banking.</small></span></div>
            <div className="art-row"><span className="art-icon"><LockKeyhole size={16} /></span><span><strong>Privacy first</strong><small>Your secrets stay yours.</small></span><Check size={17} className="check-icon" /></div>
            <div className="art-row"><span className="art-icon mint"><MessageCircle size={16} /></span><span><strong>Clear answers</strong><small>Guidance from approved FAQs.</small></span><Check size={17} className="check-icon" /></div>
          </div>
          <div className="floating-chip chip-top"><span className="chip-spark"><Sparkles size={15} /></span> Here to help</div>
          <div className="floating-chip chip-bottom"><span className="chip-check"><ShieldCheck size={15} /></span> Safety is built in</div>
        </div>
      </section>

      <section className="content-grid">
        <div className="main-column">
          <div className="section-heading"><div><span className="section-kicker">GET STARTED</span><h2>{t.quick}</h2></div><span className="heading-note">Choose a topic to begin</span></div>
          <div className="action-grid">
            {actionItems.map((item) => {
              const Icon = item.icon;
              return <button className="action-card" key={item.title} onClick={() => startChat(item.question)}>
                <span className={`action-icon ${item.tone}`}><Icon size={20} /></span><span className="action-title">{item.title}</span><span className="action-description">{item.title === "Card & PIN help" ? "Secure card guidance" : item.title === "Failed transaction" ? "Payment status & next steps" : item.title === "Account statement" ? "Find your statements" : "Pay with confidence"}</span><span className="action-arrow"><ArrowUpRight size={17} /></span>
              </button>;
            })}
          </div>
          <div className="section-heading topics-heading"><div><span className="section-kicker">POPULAR QUESTIONS</span><h2>{t.recent}</h2></div><button className="see-all" onClick={() => startChat("How can I contact customer support?")}>More help <ArrowRight size={14} /></button></div>
          <div className="topic-list">
            {[
              { icon: Clock3, title: "Where is my transaction?", desc: "Understand pending, failed, or successful payments." },
              { icon: CreditCard, title: "Lost or stolen card", desc: "Learn the safest steps to block your card." },
              { icon: CircleHelp, title: "Something else", desc: "Ask a question or create a support case." },
            ].map((item) => { const Icon = item.icon; return <button className="topic-row" key={item.title} onClick={() => item.title === "Something else" ? setCaseOpen(true) : startChat(item.title === "Lost or stolen card" ? "How do I block a lost card?" : "What should I do if a transaction failed?")}><span className="topic-icon"><Icon size={18} /></span><span className="topic-copy"><strong>{item.title}</strong><small>{item.desc}</small></span><ArrowRight size={17} className="topic-arrow" /></button>; })}
          </div>
        </div>
        <aside className="side-column">
          <div className="security-card"><div className="security-icon"><ShieldCheck size={23} /></div><span className="section-kicker">SMART & SECURE</span><h3>{t.security}</h3><p>{t.securityText}</p><div className="security-rule"><LockKeyhole size={15} /><span>We never need your secret codes.</span></div><button className="security-link" onClick={() => startChat("How do I stay safe with UPI?")}>Explore safety tips <ArrowRight size={14} /></button></div>
          <div className="human-card"><div className="human-icon"><Headphones size={20} /></div><div><h3>{t.support}</h3><p>{t.supportText}</p><button onClick={() => setCaseOpen(true)}>Create a demo case <ArrowRight size={14} /></button></div></div>
          <div className="demo-info"><span className="demo-info-icon"><LockKeyhole size={15} /></span><span><strong>Private by default</strong><small>Synthetic demo data only. No real bank account access.</small></span></div>
        </aside>
      </section>

      <footer className="footer"><a className="footer-brand" href="#"><Landmark size={16} /> smartbank<span>AI</span></a><p>{t.footer}</p><span className="footer-links">Privacy-first <span>·</span> Demo only</span></footer>

      {chatOpen && <div className="chat-panel" role="dialog" aria-label="SmartBank chat">
        <div className="chat-header"><span className="chat-avatar"><Bot size={21} /></span><div className="chat-header-copy"><strong>SmartBank Assistant</strong><small><span className="status-dot" /> AI support · Demo mode</small></div><button className="icon-button" onClick={() => setChatOpen(false)} aria-label="Close chat"><X size={19} /></button></div>
        <div className="chat-messages">
          {messages.map((message) => <div className={`message-row ${message.role}`} key={message.id}><div className="message-avatar">{message.role === "assistant" ? <Bot size={16} /> : "S"}</div><div className="message-content"><div className="message-bubble">{message.text}</div><small className="message-time">{message.time}</small></div></div>)}
          {busy && <div className="message-row assistant"><div className="message-avatar"><Bot size={16} /></div><div className="typing"><i /><i /><i /></div></div>}
          <div ref={endRef} />
        </div>
        <div className="chat-safety"><LockKeyhole size={13} /> Never share PINs, passwords, CVVs, or OTPs.</div>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); void sendMessage(); }}><input value={input} onChange={(e) => setInput(e.target.value)} placeholder={t.placeholder} aria-label="Your message" maxLength={2000} /><button type="submit" disabled={!input.trim() || busy} aria-label={t.send}><Send size={17} /></button></form>
        <div className="chat-disclaimer">Demo assistant · Verify important information with your bank.</div>
      </div>}

      {caseOpen && <div className="modal-backdrop" onClick={() => setCaseOpen(false)}><section className="case-modal" role="dialog" aria-modal="true" aria-labelledby="case-title" onClick={(e) => e.stopPropagation()}><div className="modal-heading"><div className="modal-icon"><Headphones size={21} /></div><button className="icon-button" onClick={() => setCaseOpen(false)} aria-label="Close support form"><X size={19} /></button></div><span className="section-kicker">SUPPORT CENTER</span><h2 id="case-title">How can we help?</h2><p className="modal-subtitle">Create a demo support case. It will not be sent to a real bank.</p><form onSubmit={submitCase}><label htmlFor="category">What do you need help with?</label><select id="category" value={caseCategory} onChange={(e) => setCaseCategory(e.target.value)}><option value="service">General service</option><option value="transaction">Transaction issue</option><option value="card">Card issue</option><option value="digital_banking">Digital banking</option><option value="other">Other</option></select><label htmlFor="description">Describe the issue</label><textarea id="description" value={caseDescription} onChange={(e) => setCaseDescription(e.target.value)} minLength={10} maxLength={1500} required placeholder="Tell us what happened (please do not include account numbers, PINs, or OTPs)." /><button className="primary-button modal-submit" type="submit"><Plus size={17} /> Create demo case <ArrowRight size={16} /></button></form>{caseResult && <div className="case-result" role="status">{caseResult}{caseId && <button type="button" className="security-link" onClick={() => void trackDemoCase()}>Track this case <ArrowRight size={14} /></button>}</div>}{caseTrackingResult && <div className="case-result" role="status">{caseTrackingResult}</div>}<p className="modal-footnote"><ShieldCheck size={14} /> Never include credentials or full payment-card details.</p></section></div>}
    </main>
  );
}
