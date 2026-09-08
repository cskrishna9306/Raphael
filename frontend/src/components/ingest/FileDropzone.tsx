import { useRef, useState, type ChangeEvent, type DragEvent } from "react"
import styles from "./FileDropzone.module.css"

const ACCEPTED_EXTENSIONS = [".txt", ".pdf"]

interface FileDropzoneProps {
  onFileSelected: (file: File) => void
  disabled?: boolean
}

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

export function FileDropzone({ onFileSelected, disabled }: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file && isAcceptedFile(file)) onFileSelected(file)
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) onFileSelected(file)
    event.target.value = ""
  }

  return (
    <div
      className={[styles.dropzone, isDragOver ? styles.dragOver : ""].join(" ")}
      onDragOver={(event) => {
        event.preventDefault()
        if (!disabled) setIsDragOver(true)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={disabled ? undefined : handleDrop}
    >
      <div className={styles.pageIcon} aria-hidden="true" />
      <div className={styles.instructions}>drag a .txt / .pdf&nbsp;file here</div>
      <button type="button" className={styles.browseButton} disabled={disabled} onClick={() => inputRef.current?.click()}>
        Browse files
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        className={styles.hiddenInput}
        onChange={handleInputChange}
        disabled={disabled}
      />
    </div>
  )
}
