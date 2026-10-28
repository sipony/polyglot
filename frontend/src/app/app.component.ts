import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { FileUploadModule } from 'primeng/fileupload';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { ProgressBarModule } from 'primeng/progressbar';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { CardModule } from 'primeng/card';

interface TranslationHistory {
  id: string;
  filename: string;
  targetLang: string;
  date: string;
  blobUrl?: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    FileUploadModule, ButtonModule, DropdownModule,
    CheckboxModule, ProgressBarModule, TableModule,
    ToastModule, CardModule
  ],
  providers: [MessageService],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  sourceLang = 'auto';
  targetLang = 'it';
  skipCode = true;
  selectedFile: File | null = null;
  uploading = false;
  progress = 0;
  history: TranslationHistory[] = [];

  languages = [
    { label: 'Auto-detect', value: 'auto' },
    { label: 'Italiano', value: 'it' },
    { label: 'Inglese', value: 'en' },
    { label: 'Spagnolo', value: 'es' },
    { label: 'Francese', value: 'fr' },
    { label: 'Tedesco', value: 'de' },
    { label: 'Portoghese', value: 'pt' },
    { label: 'Russo', value: 'ru' },
    { label: 'Cinese', value: 'zh-CN' },
    { label: 'Giapponese', value: 'ja' },
    { label: 'Coreano', value: 'ko' }
  ];

  // Change this to your deployed backend URL
  apiUrl = 'http://localhost:8000/translate';

  constructor(private http: HttpClient, private messageService: MessageService) {}

  ngOnInit() {
    const saved = localStorage.getItem('polyglot-history');
    if (saved) {
      this.history = JSON.parse(saved);
    }
  }

  onFileSelect(event: any) {
    this.selectedFile = event.files[0];
  }

  translate() {
    if (!this.selectedFile) {
      this.messageService.add({ severity: 'warn', summary: 'Attenzione', detail: 'Seleziona un file PDF' });
      return;
    }

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('source_lang', this.sourceLang);
    formData.append('target_lang', this.targetLang);
    formData.append('skip_code', String(this.skipCode));

    this.uploading = true;
    this.progress = 0;

    this.http.post(this.apiUrl, formData, {
      responseType: 'blob',
      reportProgress: true,
      observe: 'events'
    }).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          this.progress = Math.round(100 * event.loaded / event.total);
        } else if (event.type === HttpEventType.Response) {
          const blob = event.body as Blob;
          const url = URL.createObjectURL(blob);
          const entry: TranslationHistory = {
            id: Date.now().toString(),
            filename: this.selectedFile!.name,
            targetLang: this.targetLang,
            date: new Date().toLocaleString(),
            blobUrl: url
          };
          this.history.unshift(entry);
          this.saveHistory();
          this.uploading = false;
          this.progress = 100;
          this.messageService.add({ severity: 'success', summary: 'Completato', detail: 'PDF tradotto!' });
        }
      },
      error: (err) => {
        this.uploading = false;
        this.messageService.add({ severity: 'error', summary: 'Errore', detail: err.error?.detail || 'Traduzione fallita' });
      }
    });
  }

  download(entry: TranslationHistory) {
    if (entry.blobUrl) {
      const a = document.createElement('a');
      a.href = entry.blobUrl;
      a.download = entry.filename.replace('.pdf', `_polyglot_${entry.targetLang}.pdf`);
      a.click();
    }
  }

  clearHistory() {
    this.history.forEach(h => h.blobUrl && URL.revokeObjectURL(h.blobUrl));
    this.history = [];
    localStorage.removeItem('polyglot-history');
  }

  private saveHistory() {
    // Save without blob URLs (they are session-only)
    const toSave = this.history.map(({ blobUrl, ...rest }) => rest);
    localStorage.setItem('polyglot-history', JSON.stringify(toSave));
  }
}
