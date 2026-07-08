import { useRef, useState } from "react";
import { FileText } from "lucide-react";

interface UploadZoneProps {
  onFileUploaded: (file: File) => void;
}

export const UploadZone = ({ onFileUploaded }: UploadZoneProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) onFileUploaded(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === "application/pdf") onFileUploaded(file);
  };

  return (
    <div
      className={`upload-zone ${dragging ? "upload-zone--drag" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <div className="upload-icon-wrap">
        <FileText size={32} />
      </div>

      <h3 className="upload-heading">Upload a PDF to begin</h3>
      <p className="upload-sub">Drag &amp; drop your PDF here or click to browse</p>

      <button
        className="upload-btn"
        onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
      >
        <FileText size={15} />
        Choose PDF
      </button>

      <p className="upload-limit">Max file size: 50MB</p>

      <input
        type="file"
        accept=".pdf"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
};
