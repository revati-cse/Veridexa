"use client";

import * as monaco from "monaco-editor";
import { Editor, loader } from "@monaco-editor/react";
import { LoadingState } from "@/components/shared/LoadingState";

// Self-host Monaco's assets from our own bundle instead of fetching the AMD
// loader script from a CDN (jsdelivr) at runtime. CDN loading is a fragile
// dependency for a live demo — blocked by some networks/ad-blockers/
// firewalls, and confirmed unreachable from this project's own dev/test
// sandbox (net::ERR_TUNNEL_CONNECTION_FAILED). Self-hosting means the editor
// works offline and never depends on a third party being reachable.
loader.config({ monaco });

// Monaco's own background service (editorWorkerService) needs a Worker —
// without this, Monaco falls back to its default AMD worker-loading path,
// which doesn't resolve under Turbopack's bundling and throws on every
// mount ("Failed to resolve module specifier ...editorWebWorkerMain..."),
// even though basic editing still works without it. The `new URL(...,
// import.meta.url)` form is the one Turbopack can statically bundle as a
// worker chunk. SQL doesn't need the JSON/CSS/TS language workers — this
// single generic worker covers what editorWorkerService actually uses.
(self as unknown as { MonacoEnvironment: monaco.Environment }).MonacoEnvironment = {
  getWorker() {
    return new Worker(new URL("monaco-editor/editor/editor.worker.js", import.meta.url), {
      type: "module",
    });
  },
};

interface MonacoSqlEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function MonacoSqlEditor({ value, onChange }: MonacoSqlEditorProps) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-300">
      <Editor
        height="200px"
        language="sql"
        theme="vs"
        value={value}
        onChange={(next) => onChange(next ?? "")}
        loading={<LoadingState label="Loading code editor..." />}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          wordWrap: "on",
          tabSize: 2,
          padding: { top: 8, bottom: 8 },
        }}
      />
    </div>
  );
}
