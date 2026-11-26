
import { useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

function getAuthHeaders() {
  const token = localStorage.getItem("documind_token");

  return {
    Authorization: `Bearer ${token}`,
  };
}

function App() {
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const [backendStatus, setBackendStatus] = useState("Checking...");

  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [selectedDocument, setSelectedDocument] = useState(null);

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();

        setBackendStatus(
          response.ok ? data.message : "Backend error"
        );
      } catch {
        setBackendStatus("Backend is not connected");
      }
    }

    checkBackend();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setLoading(true);

    const endpoint =
      mode === "register"
        ? "/api/auth/register"
        : "/api/auth/login";

    const requestBody =
      mode === "register"
        ? { full_name: fullName, email, password }
        : { email, password };

    try {
      const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      if (mode === "register") {
        setMessage("Registration successful! Please log in.");
        setMode("login");
        setFullName("");
        setPassword("");
      } else {
        localStorage.setItem("documind_token", data.access_token);

        setUser(data.user);
        setMessage("");

        await loadDocuments();
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadDocuments() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents`,
        {
          headers: getAuthHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not load documents");
      }

      setDocuments(data.documents);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile) {
      setMessage("Please select a PDF first.");
      return;
    }

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents/upload`,
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setMessage("PDF uploaded successfully!");
      setSelectedFile(null);

      await loadDocuments();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleSummary(documentId) {
    setSummary("");
    setAnswer("");
    setSelectedDocument(documentId);
    setMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}/summary`,
        {
          headers: getAuthHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Summary failed");
      }

      setSummary(data.summary);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleQuestion(event) {
    event.preventDefault();

    if (!selectedDocument || !question.trim()) {
      return;
    }

    setAnswer("Finding an answer...");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
          body: JSON.stringify({
            document_id: selectedDocument,
            question,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Chat failed");
      }

      setAnswer(data.answer);
    } catch (error) {
      setAnswer(error.message);
    }
  }

  async function handleDelete(documentId) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this document?"
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Delete failed");
      }

      setMessage("Document deleted successfully!");

      setDocuments((previousDocuments) =>
        previousDocuments.filter(
          (doc) => doc.id !== documentId
        )
      );

      if (selectedDocument === documentId) {
        setSelectedDocument(null);
        setSummary("");
        setAnswer("");
        setQuestion("");
      }
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleDownload(documentId) {
    try {
      setMessage("Preparing PDF download...");

      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}/download`,
        {
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        let errorMessage = "Download failed";

        try {
          const data = await response.json();
          errorMessage = data.detail || errorMessage;
        } catch {
          // Keep the default error message.
        }

        throw new Error(errorMessage);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = "document.pdf";

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);

      setMessage("PDF downloaded successfully!");
    } catch (error) {
      setMessage(error.message);
    }
  }

  function handleLogout() {
    localStorage.removeItem("documind_token");

    setUser(null);
    setPassword("");
    setDocuments([]);
    setSummary("");
    setAnswer("");
    setQuestion("");
    setSelectedDocument(null);
    setSelectedFile(null);
    setMessage("You have logged out successfully.");
  }

  return (
    <div className="setup-page">
      {!user ? (
        <div className="setup-card">
          <div className="brand-badge">DocuMind</div>

          <h1>AI Document Assistant</h1>

          <p className="subtitle">
            Upload documents, understand their content,
            and get answers.
          </p>

          <div className="auth-tabs">
            <button
              className={mode === "login" ? "active-tab" : ""}
              onClick={() => {
                setMode("login");
                setMessage("");
              }}
            >
              Login
            </button>

            <button
              className={mode === "register" ? "active-tab" : ""}
              onClick={() => {
                setMode("register");
                setMessage("");
              }}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {mode === "register" && (
              <div className="form-group">
                <label>Full Name</label>

                <input
                  type="text"
                  placeholder="Enter your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  minLength={2}
                  maxLength={100}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label>Email Address</label>

              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>

              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                maxLength={128}
                required
              />
            </div>

            <button
              className="submit-button"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : mode === "register"
                  ? "Create Account"
                  : "Login"}
            </button>
          </form>

          {message && (
            <div className="message-box">{message}</div>
          )}

          <div className="backend-info">
            Backend Status: {backendStatus}
          </div>
        </div>
      ) : (
        <div className="dashboard">
          <header className="dashboard-header">
            <div>
              <div className="brand-badge">DocuMind</div>

              <h1>Your Document Workspace</h1>

              <p className="subtitle">
                Welcome back, {user.full_name}!
              </p>
            </div>

            <button
              className="logout-button"
              onClick={handleLogout}
            >
              Logout
            </button>
          </header>

          <section className="dashboard-panel">
            <h2>Upload a PDF</h2>

            <p className="subtitle">
              Choose a PDF document to extract and explore its content.
            </p>

            <form
              onSubmit={handleUpload}
              className="upload-form"
            >
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(e) =>
                  setSelectedFile(e.target.files[0] || null)
                }
              />

              <button
                className="submit-button"
                disabled={uploading}
              >
                {uploading ? "Uploading..." : "Upload PDF"}
              </button>
            </form>
          </section>

          {message && (
            <div className="message-box">{message}</div>
          )}

          <section className="dashboard-panel">
            <div className="section-heading">
              <h2>Your Documents</h2>

              <button
                className="refresh-button"
                onClick={loadDocuments}
              >
                Refresh
              </button>
            </div>

            {documents.length === 0 ? (
              <p className="empty-state">
                No documents uploaded yet. Upload your first PDF above.
              </p>
            ) : (
              <div className="document-list">
                {documents.map((doc) => (
                  <div
                    className="document-item"
                    key={doc.id}
                  >
                    <div>
                      <strong>{doc.original_filename}</strong>
                      <p>{doc.total_pages} pages</p>
                    </div>

                    <button
                      className="action-button"
                      onClick={() => handleSummary(doc.id)}
                    >
                      View Summary
                    </button>

                    <button
                      className="action-button"
                      onClick={() => {
                        setSelectedDocument(doc.id);
                        setSummary("");
                        setAnswer("");
                        setQuestion("");
                      }}
                    >
                      Ask Questions
                    </button>

                    <button
                      className="action-button"
                      onClick={() => handleDownload(doc.id)}
                    >
                      Download
                    </button>

                    <button
                      className="action-button"
                      onClick={() => handleDelete(doc.id)}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {summary && (
            <section className="dashboard-panel">
              <h2>Document Summary</h2>

              <p className="result-text">{summary}</p>
            </section>
          )}

          {selectedDocument && (
            <section className="dashboard-panel">
              <h2>Chat with your PDF</h2>

              <p className="subtitle">
                Ask a question about the selected document.
              </p>

              <form
                onSubmit={handleQuestion}
                className="chat-form"
              >
                <input
                  type="text"
                  placeholder="Example: What is this document about?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  required
                />

                <button className="submit-button">
                  Ask
                </button>
              </form>

              {answer && (
                <div className="answer-box">{answer}</div>
              )}
            </section>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
