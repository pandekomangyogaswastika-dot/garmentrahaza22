{
  "meta": {
    "product": "PT Rahaza ERP",
    "module": "BOM Configuration (Multi-Version + Size-specific)",
    "language": "id-ID",
    "design_style": ["glassmorphism", "industrial-dashboard", "dense-but-readable"],
    "notes": [
      "Gunakan shadcn/ui dari /app/frontend/src/components/ui (file .jsx).",
      "Tidak ada React Router: navigasi berbasis state (stepper/tabs).",
      "Semua elemen interaktif & info penting WAJIB punya data-testid (kebab-case)."
    ]
  },

  "brand_attributes": {
    "keywords": ["presisi", "terpercaya", "cepat dipindai", "siap produksi", "audit-friendly"],
    "tone": {
      "microcopy": "ringkas, operasional, tanpa jargon teknis berlebihan",
      "error_messages": "jelas + tindakan berikutnya (contoh: 'Qty KG wajib diisi. Gunakan angka desimal, mis. 1.25')"
    }
  },

  "design_tokens": {
    "typography": {
      "font_pairing": {
        "display": "Space Grotesk (sudah ada di index.css)",
        "body": "Inter (sudah ada di index.css)",
        "mono": "JetBrains Mono (sudah ada di index.css)"
      },
      "scale_tailwind": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl font-display tracking-tight",
        "h2": "text-base md:text-lg text-foreground/80",
        "section_title": "text-lg md:text-xl font-display",
        "body": "text-sm md:text-base text-foreground/85",
        "caption": "text-xs text-muted-foreground",
        "table": "text-xs md:text-sm"
      },
      "numbers": {
        "use_mono_for": ["kode material", "qty", "versi", "hasil kalkulasi"],
        "class": "font-mono tabular-nums"
      }
    },

    "color_system": {
      "mode": "ikuti token existing di /app/frontend/src/index.css (dark=Galaxy Glass, light=Lavender Clean)",
      "semantic_usage": {
        "primary": "aksi utama: Simpan Versi, Aktifkan Versi",
        "accent": "aksi cepat non-destruktif: Tambah Material, Salin ke Size",
        "success": "status aktif/valid",
        "warning": "perubahan belum disimpan / konflik versi",
        "destructive": "hapus baris material / nonaktifkan versi"
      },
      "status_badges": {
        "active": "bg-[hsl(var(--success)/0.18)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.25)]",
        "inactive": "bg-[hsl(var(--muted)/0.6)] text-muted-foreground border-border",
        "draft": "bg-[hsl(var(--warning)/0.18)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.25)]"
      },
      "diff_colors_for_compare": {
        "added": "bg-[hsl(var(--success)/0.14)] border-[hsl(var(--success)/0.22)]",
        "modified": "bg-[hsl(var(--warning)/0.14)] border-[hsl(var(--warning)/0.22)]",
        "removed": "bg-[hsl(var(--destructive)/0.12)] border-[hsl(var(--destructive)/0.22)]"
      }
    },

    "glass_surfaces": {
      "rules": [
        "Glass hanya untuk container/panel besar (card, header, side panel).",
        "Jaga keterbacaan: gunakan border tipis + shadow lembut.",
        "Maks 2 layer glass bertumpuk (mis. page header + dialog)."
      ],
      "classes": {
        "panel": "bg-[var(--card-surface)] border border-[var(--glass-border)] backdrop-blur-[var(--glass-blur)] shadow-[var(--shadow-card)] rounded-[var(--radius-md)]",
        "panel_hover": "hover:bg-[var(--card-surface-hover)] transition-colors duration-200",
        "toolbar": "bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-[var(--glass-blur)] rounded-[var(--radius-sm)]",
        "input_wrap": "bg-[var(--input-surface)] border border-[var(--glass-border)] rounded-[var(--radius-sm)]"
      }
    },

    "spacing_layout": {
      "page_container": "px-4 sm:px-6 lg:px-8 py-5",
      "max_width": "max-w-7xl",
      "section_gap": "space-y-6",
      "grid": {
        "two_col": "grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6",
        "left_col": "lg:col-span-8",
        "right_col": "lg:col-span-4"
      },
      "density": {
        "principle": "ERP padat tapi tidak sesak: gunakan row height 44–48px untuk input, 36–40px untuk table rows",
        "table_row": "h-10 md:h-11"
      }
    },

    "radius_shadow": {
      "radius": {
        "card": "rounded-[var(--radius-md)]",
        "chip": "rounded-full",
        "input": "rounded-[var(--radius-sm)]"
      },
      "shadow": {
        "card": "shadow-[var(--shadow-card)]",
        "focus": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      }
    }
  },

  "information_architecture": {
    "navigation_model": {
      "type": "state-based",
      "primary_flow": [
        "Pilih Model",
        "Pilih Size",
        "Input Material (Benang + Aksesoris)",
        "Simpan sebagai Versi Baru"
      ],
      "recommended_pattern": "Tabs + sticky action bar",
      "tabs": [
        {"key": "matrix", "label": "Matriks BOM"},
        {"key": "editor", "label": "Editor BOM"},
        {"key": "versions", "label": "Versi"},
        {"key": "preview", "label": "Preview Kebutuhan"}
      ]
    },

    "page_structures": {
      "bom_matrix_view": {
        "goal": "cek status BOM per size untuk model terpilih + akses cepat ke editor",
        "layout": [
          "Header glass: judul + model selector + search",
          "Matrix table: size sebagai kolom, status versi aktif sebagai badge",
          "Quick actions per cell: 'Buka', 'Salin dari size lain'"
        ]
      },
      "bom_editor_form": {
        "goal": "input material + simpan versi",
        "layout": [
          "Left (8/12): form material (tabs: Benang, Aksesoris)",
          "Right (4/12): panel Versi Aktif + ringkasan + tombol Simpan",
          "Sticky bottom action bar di mobile: Simpan, Preview"
        ],
        "form_pattern": "Editable table rows + inline add material (select existing / create new)"
      },
      "version_management_panel": {
        "goal": "lihat daftar versi, aktif/nonaktif, bandingkan, duplikasi",
        "layout": [
          "List versi (left) + detail versi (right) pada desktop",
          "Mobile: accordion/collapsible per versi"
        ]
      },
      "material_requirements_preview": {
        "goal": "kalkulasi kebutuhan material untuk X pcs",
        "layout": [
          "Input quantity (pcs) + opsi rounding",
          "Output: tabel ringkas total per material + subtotal per kategori",
          "CTA: Export CSV (opsional)"
        ]
      }
    }
  },

  "components": {
    "component_path": {
      "glass": ["/app/frontend/src/components/ui/glass.jsx"],
      "tabs": ["/app/frontend/src/components/ui/tabs.jsx"],
      "table": ["/app/frontend/src/components/ui/table.jsx"],
      "select": ["/app/frontend/src/components/ui/select.jsx"],
      "dialog": ["/app/frontend/src/components/ui/dialog.jsx"],
      "drawer": ["/app/frontend/src/components/ui/drawer.jsx"],
      "popover": ["/app/frontend/src/components/ui/popover.jsx"],
      "command": ["/app/frontend/src/components/ui/command.jsx"],
      "switch": ["/app/frontend/src/components/ui/switch.jsx"],
      "badge": ["/app/frontend/src/components/ui/badge.jsx"],
      "button": ["/app/frontend/src/components/ui/button.jsx"],
      "input": ["/app/frontend/src/components/ui/input.jsx"],
      "textarea": ["/app/frontend/src/components/ui/textarea.jsx"],
      "separator": ["/app/frontend/src/components/ui/separator.jsx"],
      "scroll_area": ["/app/frontend/src/components/ui/scroll-area.jsx"],
      "collapsible": ["/app/frontend/src/components/ui/collapsible.jsx"],
      "toggle_group": ["/app/frontend/src/components/ui/toggle-group.jsx"],
      "tooltip": ["/app/frontend/src/components/ui/tooltip.jsx"],
      "sonner_toast": ["/app/frontend/src/components/ui/sonner.jsx"]
    },

    "bom_specific_composites": {
      "BOMHeaderBar": {
        "description": "Header glass dengan breadcrumb + model/size selector + status versi aktif",
        "use": ["GlassPanel", "Breadcrumb", "Select", "Badge", "Button"],
        "data_testids": [
          "bom-header-model-select",
          "bom-header-size-select",
          "bom-header-active-version-badge",
          "bom-header-open-versions-button"
        ]
      },
      "VersionRail": {
        "description": "Panel kanan: daftar versi + aksi aktif/nonaktif + compare",
        "use": ["GlassPanel", "ScrollArea", "Badge", "Button", "Switch", "Tooltip"],
        "interaction": "Klik versi -> load detail; tombol 'Aktifkan' memunculkan confirm dialog",
        "data_testids": [
          "version-rail",
          "version-rail-create-version-button",
          "version-rail-activate-version-button",
          "version-rail-deactivate-version-button",
          "version-rail-compare-button"
        ]
      },
      "MaterialEditableTable": {
        "description": "Tabel editable untuk Benang/Aksesoris dengan row actions",
        "use": ["Table", "Input", "Select", "Popover", "Command", "Button", "Tooltip"],
        "row_actions": ["hapus", "duplikasi baris", "catatan"],
        "data_testids": [
          "material-table",
          "material-table-add-row-button",
          "material-table-row-delete-button",
          "material-table-row-duplicate-button",
          "material-table-inline-material-picker"
        ]
      },
      "InlineMaterialPicker": {
        "description": "Pilih material dari master data (Command) atau tambah baru (Dialog/Drawer)",
        "pattern": "Popover -> Command list; footer action 'Tambah material baru' membuka Drawer di mobile, Dialog di desktop",
        "data_testids": [
          "inline-material-picker-trigger",
          "inline-material-picker-search-input",
          "inline-material-picker-create-new-button",
          "inline-material-create-form-submit-button"
        ]
      },
      "RequirementsPreviewCard": {
        "description": "Kalkulator kebutuhan material untuk X pcs + tabel hasil",
        "use": ["GlassPanel", "Input", "Tabs", "Table", "Badge", "Button"],
        "data_testids": [
          "requirements-qty-input",
          "requirements-preview-table",
          "requirements-export-csv-button"
        ]
      },
      "VersionCompareView": {
        "description": "Side-by-side compare versi (opsional) dengan highlight added/modified/removed",
        "use": ["Tabs", "Table", "Badge", "ToggleGroup", "ScrollArea"],
        "data_testids": [
          "version-compare-view",
          "version-compare-left-select",
          "version-compare-right-select",
          "version-compare-diff-toggle"
        ]
      }
    }
  },

  "interaction_motion": {
    "principles": [
      "Micro-interactions wajib: hover, pressed, focus ring, loading skeleton.",
      "Tidak pakai transition: all. Gunakan transition-colors / transition-opacity / transition-shadow.",
      "Prefer reduced motion: hormati prefers-reduced-motion (sudah ada di index.css)."
    ],
    "patterns": {
      "sticky_action_bar_mobile": {
        "description": "Di mobile, tombol Simpan/Preview selalu terlihat",
        "classes": "fixed bottom-3 left-3 right-3 z-[var(--z-dropdown)]",
        "surface": "bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-[var(--glass-blur)] shadow-[var(--shadow-soft)] rounded-[var(--radius-lg)]",
        "motion": "animate-in slide-in-from-bottom-2 duration-200"
      },
      "row_hover": {
        "classes": "hover:bg-[hsl(var(--foreground)/0.04)] transition-colors duration-200",
        "note": "Di dark mode gunakan hover opacity kecil agar tidak 'bercak'."
      },
      "save_feedback": {
        "use": "sonner toast",
        "messages": {
          "success": "Versi BOM berhasil disimpan.",
          "error": "Gagal menyimpan. Periksa koneksi atau field wajib.",
          "dirty": "Ada perubahan belum disimpan. Simpan sebagai versi baru?"
        }
      }
    }
  },

  "data_display_patterns": {
    "matrix_table": {
      "description": "Matriks size vs status BOM",
      "columns": ["Size", "Versi Aktif", "Terakhir Update", "Aksi"],
      "cell_badges": ["Aktif", "Draft", "Belum ada"],
      "empty_state": {
        "title": "Belum ada BOM untuk model ini",
        "body": "Pilih size lalu buat versi BOM pertama.",
        "cta": "Buat Versi Pertama"
      }
    },
    "editable_tables": {
      "yarn_columns": ["Kode", "Nama", "Tipe Benang", "Qty (KG)", "Catatan", "Aksi"],
      "accessory_columns": ["Kode", "Nama", "Qty", "Unit", "Catatan", "Aksi"],
      "validation": {
        "qty_kg": "min 0, boleh desimal",
        "qty": "min 0",
        "unit": "wajib pilih dari select"
      }
    }
  },

  "accessibility": {
    "requirements": [
      "Kontras teks vs glass surface harus aman (gunakan token foreground/muted-foreground).",
      "Semua input punya Label (shadcn Label) + aria-describedby untuk helper/error.",
      "Keyboard: Tab order jelas; Command list bisa dinavigasi panah.",
      "Focus visible ring jangan dihapus."
    ],
    "touch_targets": {
      "min": "44px",
      "apply_to": ["ikon hapus baris", "toggle aktif", "menu versi"]
    }
  },

  "image_urls": {
    "usage_rules": [
      "ERP bukan landing page: gambar hanya sebagai dekorasi halus (maks 10–15% area header) atau empty state.",
      "Jangan taruh foto di area tabel/form (mengganggu keterbacaan)."
    ],
    "header_ambient": [
      {
        "category": "header",
        "description": "Foto pabrik tekstil untuk header kecil (blur + opacity rendah) sebagai konteks industri",
        "url": "https://images.pexels.com/photos/31047139/pexels-photo-31047139.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
      }
    ],
    "empty_state_texture": [
      {
        "category": "empty-state",
        "description": "Tekstur benang/serat untuk empty state (blur 12–18px, opacity 0.12–0.18)",
        "url": "https://images.unsplash.com/photo-1611584414353-697cb0efe20f?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "empty-state",
        "description": "Tekstur rope untuk variasi empty state (lebih netral)",
        "url": "https://images.unsplash.com/photo-1584046612867-8aa525ac3810?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "implementation_notes_for_main_agent": {
    "react_js_conventions": [
      "Gunakan .jsx (bukan .tsx).",
      "Komponen reusable: named export. Page: default export.",
      "Tidak ada React Router: gunakan state `activeTab`, `selectedModel`, `selectedSize`, `activeVersionId`.",
      "Gunakan `sonner` untuk toast (lihat /app/frontend/src/components/ui/sonner.jsx)."
    ],
    "data_testid_convention": {
      "format": "kebab-case",
      "examples": [
        "bom-model-select",
        "bom-size-select",
        "bom-save-new-version-button",
        "bom-version-activate-button",
        "bom-yarn-add-row-button",
        "bom-preview-qty-input"
      ]
    },
    "suggested_state_model": {
      "entities": ["model", "size", "bomVersion", "materialMaster"],
      "ui_state": ["activeTab", "isDirty", "isSaving", "compareMode"],
      "versioning_rules": [
        "Versi aktif hanya satu per model+size.",
        "Edit diperbolehkan untuk versi aktif (sesuai requirement).",
        "Saat ada perubahan: tampilkan badge 'Belum disimpan' + toast saat pindah tab/size."
      ]
    },
    "nice_to_have": [
      "Version compare: pilih 2 versi -> tampilkan diff highlight.",
      "Copy BOM to other sizes: tempatkan sebagai action di VersionRail (Button + Dialog confirm)."
    ]
  },

  "references": {
    "inspiration_links": [
      "https://dribbble.com/search/glassmorphism-dashboard",
      "https://dribbble.com/search/erp-settings",
      "https://www.behance.net/search/projects/erp%20ui%20design%20web",
      "https://my.altium.com/altium-365/getting-started/bom-compare",
      "https://help.openbom.com/my-openbom/bom-compare/"
    ],
    "notes": [
      "Ambil pola compare BOM dari tool engineering (Altium/OpenBOM): side-by-side + delta highlight.",
      "Gunakan glassmorphism secara disiplin: fokus pada keterbacaan tabel & form."
    ]
  },

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
