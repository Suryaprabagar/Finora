/**
 * Web Crypto API utilities for AES-256-GCM encryption with PBKDF2 key derivation.
 */

const ITERATIONS = 100000;
const SALT_SIZE = 16;
const IV_SIZE = 12;

/**
 * Derives an AES-GCM key from a password and salt using PBKDF2.
 */
async function deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    { name: "PBKDF2" },
    false,
    ["deriveBits", "deriveKey"]
  );

  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt,
      iterations: ITERATIONS,
      hash: "SHA-256"
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

/**
 * Encrypts a JSON object into a Base64 string containing the salt, IV, and cipher text.
 */
export async function encryptData(data: object, password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_SIZE));
  const iv = crypto.getRandomValues(new Uint8Array(IV_SIZE));
  const key = await deriveKey(password, salt);

  const enc = new TextEncoder();
  const encodedData = enc.encode(JSON.stringify(data));

  const cipherText = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: iv
    },
    key,
    encodedData
  );

  // Pack the payload: [ salt (16 bytes) | iv (12 bytes) | cipherText ]
  const payload = new Uint8Array(salt.length + iv.length + cipherText.byteLength);
  payload.set(salt, 0);
  payload.set(iv, salt.length);
  payload.set(new Uint8Array(cipherText), salt.length + iv.length);

  // Convert to Base64 for easier transport/storage
  return btoa(String.fromCharCode(...new Uint8Array(payload)));
}

/**
 * Decrypts a Base64 string back into a JSON object.
 */
export async function decryptData(encryptedBase64: string, password: string): Promise<any> {
  const payloadStr = atob(encryptedBase64);
  const payload = new Uint8Array(payloadStr.length);
  for (let i = 0; i < payloadStr.length; i++) {
    payload[i] = payloadStr.charCodeAt(i);
  }

  const salt = payload.slice(0, SALT_SIZE);
  const iv = payload.slice(SALT_SIZE, SALT_SIZE + IV_SIZE);
  const cipherText = payload.slice(SALT_SIZE + IV_SIZE);

  const key = await deriveKey(password, salt);

  const decryptedData = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: iv
    },
    key,
    cipherText
  );

  const dec = new TextDecoder();
  return JSON.parse(dec.decode(decryptedData));
}
