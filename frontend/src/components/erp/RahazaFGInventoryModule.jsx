import { useState, useEffect, useCallback } from 'react';
import { Archive, Package, Search, TrendingUp, TrendingDown, ChevronRight, RefreshCw, Download } from 'lucide-react';
import { GlassCard, GlassPanel, GlassInput } from '@/components/ui/glass';
import { Button } from '@/components/ui/button';

/**
 * RahazaFGInventoryModule
 * Inventory Produk Jadi (Finished Goods) — terpisah dari Inventory Bahan & Aksesoris.
 * Menampilkan stok FG (type=fg) yang otomatis bertambah dari output Packing.
 */
export default function RahazaFGInventoryModule({ token }) {
  const [items, setItems]     = useState([]);
  const [stocks, setStocks]   = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState('');
  const [updatedAt, setUpdatedAt] = useState('');

  const h = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch FG materials
      const params = new URLSearchParams({ type: 'fg' });
      if (search) params.set('search', search);
      const [matRes, stockRes] = await Promise.all([
        fetch(`/api/rahaza/materials?${params}`, { headers: h }),
        fetch('/api/rahaza/material-stock', { headers: h }),
      ]);
      if (matRes.ok) setItems(await matRes.json());
      if (stockRes.ok) {
        const stockData = await stockRes.json();
        // Build map: material_id → qty (sum all locations)
        const map = {};
        (Array.isArray(stockData) ? stockData : (stockData.rows || [])).forEach(s => {
          if (!map[s.material_id]) map[s.material_id] = 0;
          map[s.material_id] += (s.qty || 0);
        });
        setStocks(map);
      }
      setUpdatedAt(new Date().toLocaleTimeString('id-ID'));
    } finally { setLoading(false); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, search]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const totalFGQty = items.reduce((acc, m) => acc + (stocks[m.id] || 0), 0);
  const totalFGItems = items.length;
  const totalStocked = items.filter(m => (stocks[m.id] || 0) > 0).length;

  return (
    <div className="space-y-5" data-testid="fg-inventory-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Archive className="w-6 h-6 text-emerald-400" />
            Inventory Produk Jadi
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Stok barang jadi (FG) yang dihasilkan dari proses Packing.
            Terpisah dari inventory bahan baku & aksesoris.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={fetchData} className="gap-1.5 text-xs">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {updatedAt && <span className="text-xs text-muted-foreground">Diperbarui: {updatedAt}</span>}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">Total Item SKU</div>
          <div className="text-2xl font-bold text-foreground">{totalFGItems}</div>
        </GlassPanel>
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">SKU Punya Stok</div>
          <div className="text-2xl font-bold text-emerald-400">{totalStocked}</div>
        </GlassPanel>
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">Total Qty On Hand</div>
          <div className="text-2xl font-bold text-primary">{totalFGQty.toLocaleString('id-ID')} pcs</div>
        </GlassPanel>
      </div>

      {/* Search & Table */}
      <GlassCard className="p-0 overflow-hidden">
        <div className="flex items-center gap-3 p-4 border-b border-[var(--glass-border)]">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <GlassInput
              placeholder="Cari produk jadi…"
              className="pl-8 h-8 text-sm"
              value={search}
              onChange={e => setSearch(e.target.value)}
              data-testid="fg-search"
            />
          </div>
          <span className="text-xs text-muted-foreground ml-auto">{items.length} produk</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 space-y-2">
            <Archive className="w-10 h-10 mx-auto text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">Belum ada produk jadi.</p>
            <p className="text-xs text-muted-foreground/70">
              Produk jadi otomatis muncul saat output Packing dicatat di modul Eksekusi Proses.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[11px] text-muted-foreground border-b border-[var(--glass-border)] bg-[var(--glass-bg)]">
                  <th className="px-4 py-2.5 text-left font-medium">Kode FG</th>
                  <th className="px-4 py-2.5 text-left font-medium">Nama Produk</th>
                  <th className="px-4 py-2.5 text-center font-medium">Stok (pcs)</th>
                  <th className="px-4 py-2.5 text-center font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map(m => {
                  const qty = stocks[m.id] || 0;
                  const hasStock = qty > 0;
                  return (
                    <tr key={m.id} className="border-t border-[var(--glass-border)] hover:bg-[var(--glass-bg)] transition-colors">
                      <td className="px-4 py-2.5">
                        <span className="font-mono text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded">
                          {m.code}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="font-medium text-foreground">{m.name}</div>
                        {m.notes && <div className="text-xs text-muted-foreground">{m.notes}</div>}
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`text-base font-bold ${hasStock ? 'text-emerald-400' : 'text-muted-foreground/50'}`}>
                          {qty.toLocaleString('id-ID')}
                        </span>
                        <span className="text-xs text-muted-foreground ml-1">pcs</span>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        {hasStock ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-300 bg-emerald-400/10 border border-emerald-300/20 px-2 py-0.5 rounded-full">
                            <TrendingUp className="w-3 h-3" /> Ada Stok
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-[var(--glass-bg)] border border-[var(--glass-border)] px-2 py-0.5 rounded-full">
                            <TrendingDown className="w-3 h-3" /> Kosong
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Info box */}
      <GlassPanel className="p-4 flex items-start gap-3">
        <ChevronRight className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
        <div className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Cara kerja:</span>{' '}
          Setiap kali supervisor/admin mencatat output di proses <b>Packing</b> dengan memilih Model &amp; Size,
          sistem otomatis menambahkan qty ke inventory produk jadi ini.
          Kode FG menggunakan format <code className="text-primary">FG-[KODE_MODEL]-[SIZE]</code>.
        </div>
      </GlassPanel>
    </div>
  );
}
