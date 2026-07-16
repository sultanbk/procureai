/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Client Axios library wrapping calls to the backend REST API.
 * 
 * What it means:
 * API client connecting UI actions to server endpoints.
 * 
 * Importance in Project:
 * Critical. Centralizes backend interactions, timeouts, and error handling.
 */

const API_BASE = `${import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"}/api`;
const API_KEY = import.meta.env.VITE_API_KEY;

const authFetch = (url, options = {}) => {
  const headers = new Headers(options.headers || {});
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }
  return fetch(url, {
    ...options,
    headers,
  });
};

export const uploadContract = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await authFetch(`${API_BASE}/upload/contract`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to upload contract");
  }
  return response.json();
};

export const uploadInvoice = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await authFetch(`${API_BASE}/upload/invoice`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to upload invoice");
  }
  return response.json();
};

export const runAudit = async (contractFileId, invoiceFileIds, supplierName = "", force = false) => {
  const payload = {
    contract_file_id: contractFileId,
    invoice_file_ids: invoiceFileIds,
    force: force,
  };
  if (supplierName) {
    payload.supplier_name = supplierName;
  }
  const response = await authFetch(`${API_BASE}/audit/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to initiate audit");
  }
  return response.json();
};

export const getAuditStatus = async (auditId) => {
  const response = await authFetch(`${API_BASE}/audit/${auditId}`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to fetch audit status");
  }
  return response.json();
};

export const getAudits = async () => {
  const response = await authFetch(`${API_BASE}/audits`);
  if (!response.ok) {
    throw new Error("Failed to fetch audits list");
  }
  return response.json();
};

export const deleteAudit = async (auditId) => {
  const response = await authFetch(`${API_BASE}/audit/${auditId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    if (response.status === 404) {
      // Idempotent: already deleted
      return;
    }
    throw new Error("Failed to delete audit");
  }
  return response.json();
};

export const getAuditLogs = async (auditId) => {
  const response = await authFetch(`${API_BASE}/audit/${auditId}/logs`);
  if (!response.ok) {
    throw new Error("Failed to fetch audit logs");
  }
  return response.json();
};

export const getSuppliers = async () => {
  const response = await authFetch(`${API_BASE}/suppliers`);
  if (!response.ok) {
    throw new Error("Failed to fetch suppliers");
  }
  return response.json();
};

export const getSupplierHistory = async (supplierName) => {
  const response = await authFetch(`${API_BASE}/suppliers/${encodeURIComponent(supplierName)}/history`);
  if (!response.ok) {
    throw new Error("Failed to fetch supplier history");
  }
  return response.json();
};

export const getSupplierSummary = async () => {
  const response = await authFetch(`${API_BASE}/suppliers/summary`);
  if (!response.ok) {
    throw new Error("Failed to fetch supplier summary");
  }
  return response.json();
};

export const getAnalytics = async (period = "30d") => {
  const response = await authFetch(`${API_BASE}/analytics/overview?period=${period}`);
  if (!response.ok) {
    throw new Error("Failed to fetch analytics overview");
  }
  return response.json();
};

export const getHeatmap = async (period = "30d") => {
  const response = await authFetch(`${API_BASE}/analytics/heatmap?period=${period}`);
  if (!response.ok) {
    throw new Error("Failed to fetch analytics heatmap");
  }
  return response.json();
};

export async function generateDisputeLetter(payload) {
  const response = await authFetch(`${API_BASE}/disputes/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = "Failed to generate dispute letter";
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function getDisputeLetter(auditId) {
  const response = await authFetch(`${API_BASE}/disputes/${encodeURIComponent(auditId)}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "No saved dispute letter");
  }
  return response.json();
}

export async function reviseDisputeLetter(payload) {
  const response = await authFetch(`${API_BASE}/disputes/revise`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to revise dispute letter");
  }
  return response.json();
}

export const getAuditDocuments = async (auditId) => {
  const response = await authFetch(`${API_BASE}/audit/${encodeURIComponent(auditId)}/documents`);
  if (!response.ok) throw new Error("Failed to fetch uploaded files");
  return response.json();
};

export const fetchAuditDocumentBlob = async (auditId, documentId) => {
  const response = await authFetch(`${API_BASE}/audit/${encodeURIComponent(auditId)}/documents/${encodeURIComponent(documentId)}`);
  if (!response.ok) throw new Error("Failed to open uploaded file");
  return response.blob();
};

export const downloadBreachPages = async (auditId, findingId) => {
  const response = await authFetch(`${API_BASE}/audit/${encodeURIComponent(auditId)}/breach-pages/${encodeURIComponent(findingId)}`);
  if (!response.ok) throw new Error("Failed to download breach pages");
  return response.blob();
};

export const getNotificationSettings = async () => {
  const response = await authFetch(`${API_BASE}/settings/notifications`);
  if (!response.ok) {
    throw new Error("Failed to fetch notification settings");
  }
  return response.json();
};

export const updateNotificationSettings = async (payload) => {
  const response = await authFetch(`${API_BASE}/settings/notifications`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to update notification settings");
  }
  return response.json();
};

export const testSlack = async (webhookUrl) => {
  const response = await authFetch(`${API_BASE}/settings/notifications/test-slack`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ webhook_url: webhookUrl }),
  });
  if (!response.ok) {
    throw new Error("Failed to test Slack integration");
  }
  return response.json();
};

export const testEmail = async (payload) => {
  const response = await authFetch(`${API_BASE}/settings/notifications/test-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to test Email integration");
  }
  return response.json();
};

export const chatWithContract = async (auditId, message, history) => {
  const response = await authFetch(`${API_BASE}/contracts/${auditId}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, history: history.slice(-6) }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = "Failed to start chat session";
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return response; // Caller will read the readable stream
};

export const getContracts = async (showArchived = false) => {
  const response = await authFetch(`${API_BASE}/contracts?show_archived=${showArchived}`);
  if (!response.ok) throw new Error("Failed to fetch contract library");
  return response.json();
};

export const registerContract = async (formData) => {
  const response = await authFetch(`${API_BASE}/contracts`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload contract to library");
  }
  return response.json();
};

export const deleteContract = async (contractId, permanent = false) => {
  const response = await authFetch(`${API_BASE}/contracts/${contractId}?permanent=${permanent}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to remove contract from library");
  return response.json();
};

export const restoreContract = async (contractId) => {
  const response = await authFetch(`${API_BASE}/contracts/${contractId}/restore`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to restore contract");
  return response.json();
};

export const updateContractAliases = async (contractId, aliases) => {
  const response = await authFetch(`${API_BASE}/contracts/${contractId}/aliases`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ aliases }),
  });
  if (!response.ok) throw new Error("Failed to update contract aliases");
  return response.json();
};

export const getWatcherStatus = async () => {
  const response = await authFetch(`${API_BASE}/watcher/status`);
  if (!response.ok) throw new Error("Failed to fetch watcher status");
  return response.json();
};

export const pauseWatcher = async () => {
  const response = await authFetch(`${API_BASE}/watcher/pause`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to pause file watcher");
  return response.json();
};

export const resumeWatcher = async () => {
  const response = await authFetch(`${API_BASE}/watcher/resume`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to resume file watcher");
  return response.json();
};

export const getWatcherHistory = async () => {
  const response = await authFetch(`${API_BASE}/watcher/history`);
  if (!response.ok) throw new Error("Failed to fetch auto-audit history");
  return response.json();
};

export const getUnmatchedFiles = async () => {
  const response = await authFetch(`${API_BASE}/watcher/unmatched`);
  if (!response.ok) throw new Error("Failed to fetch unmatched files");
  return response.json();
};

export const retryUnmatched = async (filename, contractId) => {
  const response = await authFetch(`${API_BASE}/watcher/retry/${encodeURIComponent(filename)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contract_id: contractId }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Manual match retry failed");
  }
  return response.json();
};

export const uploadForComparison = async (oldFile, newFile) => {
  const formData = new FormData();
  formData.append("old_contract", oldFile);
  formData.append("new_contract", newFile);

  const response = await authFetch(`${API_BASE}/compare/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload contracts for comparison");
  }
  return response.json();
};

export const getComparison = async (comparisonId) => {
  const response = await authFetch(`${API_BASE}/compare/${comparisonId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch comparison details");
  }
  return response.json();
};

export const getComparisonsList = async () => {
  const response = await authFetch(`${API_BASE}/compare`);
  if (!response.ok) {
    throw new Error("Failed to fetch comparisons list");
  }
  return response.json();
};

export const generateNegotiationBrief = async (supplierName) => {
  const response = await authFetch(`${API_BASE}/suppliers/${encodeURIComponent(supplierName)}/negotiation-brief`, {
    method: "POST"
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to generate negotiation brief");
  }
  return response.json();
};

export const getBriefs = async (supplierName) => {
  const response = await authFetch(`${API_BASE}/suppliers/${encodeURIComponent(supplierName)}/negotiation-briefs`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to fetch negotiation briefs");
  }
  return response.json();
};

export const getBrief = async (supplierName, briefId) => {
  const response = await authFetch(`${API_BASE}/suppliers/${encodeURIComponent(supplierName)}/negotiation-briefs/${encodeURIComponent(briefId)}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to fetch negotiation brief");
  }
  return response.json();
};

export const predictRisk = async (payload) => {
  const response = await authFetch(`${API_BASE}/predict/risk`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to predict risk");
  }
  return response.json();
};

export const submitFindingFeedback = async (auditId, findingId, payload) => {
  const response = await authFetch(`${API_BASE}/audit/${encodeURIComponent(auditId)}/findings/${encodeURIComponent(findingId)}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to submit finding feedback");
  }
  return response.json();
};
