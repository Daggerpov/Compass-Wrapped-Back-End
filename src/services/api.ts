import axios from 'axios';

// Environment toggle - set to false for production, true for development
export const isDevelopment = true;

// API URLs for different environments
const DEV_API_URL = 'http://localhost:8000';
const PROD_API_URL = 'https://compass-wrapped.vercel.app';

// Set the base API URL based on the environment
const API_URL = isDevelopment ? DEV_API_URL : PROD_API_URL;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
}); 