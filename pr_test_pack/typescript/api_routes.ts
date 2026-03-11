import express from "express";

const app = express();

app.get("/health", (_req, res) => {
  res.status(200).json({ ok: true });
});

export default app;
