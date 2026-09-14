import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
const API_ORIGIN = API_URL.replace(/\/api\/?$/, "");

export const mediaUrl = (value) => {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${API_ORIGIN}${value.startsWith("/") ? value : `/${value}`}`;
};

const client = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh/`, { refresh });
          localStorage.setItem("access_token", data.access);
          original.headers = original.headers || {};
          original.headers.Authorization = `Bearer ${data.access}`;
          return client(original);
        } catch (e) {
          localStorage.clear();
          window.location.href = "/connexion";
        }
      } else {
        window.location.href = "/connexion";
      }
    }
    return Promise.reject(error);
  }
);

export default client;
