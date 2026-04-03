const stripTrailingSlash = (value) => value.replace(/\/+$/, "");
function getPublicBackendApiUrl() {
  return stripTrailingSlash("http://localhost:8000/api");
}
function getServerBackendApiUrl() {
  return stripTrailingSlash("http://backend:8000/api");
}
async function fetchCurrentUser(request) {
  const cookie = request.headers.get("cookie");
  if (!cookie) {
    return null;
  }
  const response = await fetch(`${getServerBackendApiUrl()}/auth/me`, {
    headers: {
      Accept: "application/json",
      Cookie: cookie
    }
  });
  if (!response.ok) {
    return null;
  }
  return await response.json();
}

export { getServerBackendApiUrl as a, fetchCurrentUser as f, getPublicBackendApiUrl as g };
