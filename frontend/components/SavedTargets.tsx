"use client";

import { useEffect, useState } from "react";
import { Bookmark, Plus, X } from "lucide-react";

interface SavedTarget {
  label: string;
  url: string;
}

interface SavedTargetsProps {
  storageKey: string;
  currentValue: string;
  onSelect: (url: string) => void;
}

export default function SavedTargets({ storageKey, currentValue, onSelect }: SavedTargetsProps) {
  const [targets, setTargets] = useState<SavedTarget[]>([]);
  const [showNameInput, setShowNameInput] = useState(false);
  const [newLabel, setNewLabel] = useState("");

  useEffect(() => {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      try {
        setTargets(JSON.parse(raw));
      } catch {
        setTargets([]);
      }
    }
  }, [storageKey]);

  function persist(list: SavedTarget[]) {
    setTargets(list);
    localStorage.setItem(storageKey, JSON.stringify(list));
  }

  function handleSave() {
    if (!currentValue.trim()) return;
    const label = newLabel.trim() || currentValue.trim();
    const withoutDuplicate = targets.filter((t) => t.url !== currentValue.trim());
    persist([...withoutDuplicate, { label, url: currentValue.trim() }]);
    setNewLabel("");
    setShowNameInput(false);
  }

  function handleRemove(url: string) {
    persist(targets.filter((t) => t.url !== url));
  }

  return (
    <div className="mt-2">
      <div className="flex flex-wrap items-center gap-1.5">
        {targets.map((t) => (
          <span
            key={t.url}
            className="group inline-flex items-center gap-1.5 text-xs bg-bg border border-bg-border rounded-full pl-3 pr-1.5 py-1 cursor-pointer hover:border-brand-red/40"
          >
            <button type="button" onClick={() => onSelect(t.url)} className="text-gray-300 group-hover:text-white">
              <Bookmark size={10} className="inline mr-1 -mt-0.5 text-brand-red" />
              {t.label}
            </button>
            <button
              type="button"
              onClick={() => handleRemove(t.url)}
              className="text-gray-600 hover:text-severity-critical rounded-full p-0.5"
              title="Remover"
            >
              <X size={11} />
            </button>
          </span>
        ))}

        {!showNameInput ? (
          <button
            type="button"
            onClick={() => setShowNameInput(true)}
            disabled={!currentValue.trim()}
            className="text-xs text-gray-500 hover:text-brand-red disabled:opacity-30 flex items-center gap-1"
          >
            <Plus size={11} /> Salvar este projeto
          </button>
        ) : (
          <span className="inline-flex items-center gap-1.5">
            <input
              autoFocus
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              placeholder="Apelido (opcional)"
              className="text-xs bg-bg border border-bg-border rounded-full px-3 py-1 text-gray-200 w-36 focus:outline-none focus:border-brand-red/50"
            />
            <button type="button" onClick={handleSave} className="text-xs text-brand-red hover:underline">Salvar</button>
            <button type="button" onClick={() => setShowNameInput(false)} className="text-xs text-gray-600 hover:text-gray-400">cancelar</button>
          </span>
        )}
      </div>
    </div>
  );
}
