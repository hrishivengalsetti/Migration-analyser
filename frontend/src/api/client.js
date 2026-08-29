export async function uploadRun(originalFile, migratedFile) {
  if (!originalFile || !migratedFile) {
    throw new Error('Both original and migrated codebase ZIP files are required.');
  }

  if (!originalFile.name.endsWith('.zip') || !migratedFile.name.endsWith('.zip')) {
    throw new Error('Both files must be .zip archives.');
  }

  const formData = new FormData();
  formData.append('original', originalFile);
  formData.append('migrated', migratedFile);

  try {
    const res = await fetch('/api/runs', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      let errorMessage = `Upload failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        }
      } catch (_) {
        // ignore json parse error
      }
      throw new Error(errorMessage);
    }

    return await res.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to the backend server.');
    }
    throw err;
  }
}

export async function getRunStatus(runId) {
  if (!runId) {
    throw new Error('Run ID is required.');
  }

  try {
    const res = await fetch(`/api/runs/${runId}`);

    if (!res.ok) {
      let errorMessage = `Failed to get run status (${res.status})`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch (_) {
        // ignore json parse error
      }
      throw new Error(errorMessage);
    }

    return await res.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Network error: Server lost connection during polling.');
    }
    throw err;
  }
}

export async function getReport(runId) {
  if (!runId) {
    throw new Error('Run ID is required.');
  }

  try {
    const res = await fetch(`/api/runs/${runId}/report`);

    if (!res.ok) {
      let errorMessage = `Failed to fetch report (${res.status})`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch (_) {
        // ignore json parse error
      }
      throw new Error(errorMessage);
    }

    return await res.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Network error: Unable to load report from server.');
    }
    throw err;
  }
}
