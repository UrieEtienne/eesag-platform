import axios from "axios";

// En développement, toujours passer par le proxy Vite /api.
// Cela évite de mélanger localhost et 127.0.0.1 et supprime les erreurs CORS locales.
const configuredApi = import.meta.env.VITE_API_URL || "";
const API_URL = import.meta.env.DEV ? "/api" : (configuredApi || "/api");
const API_ORIGIN = API_URL.startsWith("http") ? API_URL.replace(/\/api\/?$/, "") : "";

export const mediaUrl = (value) => {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  if (value.startsWith("/media/")) return value;
  return API_ORIGIN ? `${API_ORIGIN}${value.startsWith("/") ? value : `/${value}`}` : (value.startsWith("/") ? value : `/${value}`);
};

const client = axios.create({ baseURL: API_URL, timeout: 15000, headers: { Accept: "application/json" } });
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
client.interceptors.response.use((r)=>r, async (error)=>{
  const original=error.config;
  if(error.response?.status===401 && original && !original._retry){
    original._retry=true;
    const refresh=localStorage.getItem("refresh_token");
    if(refresh){
      try{
        const {data}=await axios.post(`${API_URL}/auth/refresh/`,{refresh});
        localStorage.setItem("access_token",data.access);
        original.headers=original.headers||{};
        original.headers.Authorization=`Bearer ${data.access}`;
        return client(original);
      }catch{ localStorage.clear(); window.location.href="/connexion"; }
    } else { localStorage.clear(); window.location.href="/connexion"; }
  }
  return Promise.reject(error);
});
export default client;
