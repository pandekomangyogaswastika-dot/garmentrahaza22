import { useState, useEffect, useCallback } from 'react';
import {
  Archive, Package, Search, TrendingUp, TrendingDown, ChevronRight,
  RefreshCw, ArrowDownCircle, ArrowUpCircle, Activity, Info
} from 'lucide-react';
import { GlassCard, GlassPanel, GlassInput } from '@/components/ui/glass';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

/**
 * RahazaFGInventoryModule
 * Inventory Produk Jadi (Finished Goods) — terpisah dari Inventory Bahan & Aksesoris.
 *
 * FLOW STOCK:
 *  INTERNAL   : WO selesai (bundle "packed") → FG stock +qty
 *  CUSTOMER PO: WO selesai (bundle "packed") → FG stock +qty → Shipment dispatch → FG stock -qty
 */
export default function RahazaFGInventoryModule({ token }) {
  const [items, setItems]       = useState([]);
  const [stocks, setStocks]     = useState({});
  const [movements, setMovements] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [updatedAt, setUpdatedAt] = useState('');
  const [activeTab, setActiveTab] = useState('stock');

  const h = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ type: 'fg' });
      if (search) params.set('search', search);
      const [matRes, stockRes, movRes] = await Promise.all([
        fetch(`/api/rahaza/materials?${params}`, { headers: h }),
        fetch('/api/rahaza/material-stock', { headers: h }),
        fetch('/api/rahaza/fg-movements?limit=50', { headers: h }),
      ]);
      if (matRes.ok)   setItems(await matRes.json());
      if (movRes.ok)   setMovements(await movRes.json());
      if (stockRes.ok) {
        const sd = await stockRes.json();
        const map = {};
        (Array.isArray(sd) ? sd : (sd.rows || [])).forEach(s => {
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

  const totalFGQty    = items.reduce((acc, m) => acc + (stocks[m.id] || 0), 0);
  const totalStocked  = items.filter(m => (stocks[m.id] || 0) > 0).length;
  const inboundToday  = movements.filter(mv => {
    const d = new Date(mv.timestamp);
    return mv.direction === 'in' && d.toDateString() === new Date().toDateString();
  }).reduce((a, mv) => a + (mv.qty || 0), 0);
  const outboundToday = movements.filter(mv => {
    const d = new Date(mv.timestamp);
    return mv.direction === 'out' && d.toDateString() === new Date().toDateString();
  }).reduce((a, mv) => a + (mv.qty || 0), 0);

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
            Stok barang jadi (FG) dari proses produksi — Internal & Customer PO.
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">Total SKU</div>
          <div className="text-2xl font-bold text-foreground">{items.length}</div>
          <div className="text-[10px] text-muted-foreground">terdaftar</div>
        </GlassPanel>
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">Total Qty On Hand</div>
          <div className="text-2xl font-bold text-primary">{totalFGQty.toLocaleString('id-ID')}</div>
          <div className="text-[10px] text-muted-foreground">pcs tersedia</div>
        </GlassPanel>
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1 flex items-center justify-center gap-1">
            <ArrowDownCircle className="w-3 h-3 text-emerald-400" /> Masuk Hari Ini
          </div>
          <div className="text-2xl font-bold text-emerald-400">+{inboundToday.toLocaleString('id-ID')}</div>
          <div className="text-[10px] text-muted-foreground">pcs dari produksi</div>
        </GlassPanel>
        <GlassPanel className="p-4 text-center">
          <div className="text-[10px] text-muted-foreground uppercase mb-1 flex items-center justify-center gap-1">
            <ArrowUpCircle className="w-3 h-3 text-rose-400" /> Keluar Hari Ini
          </div>
          <div className="text-2xl font-bold text-rose-400">-{outboundToday.toLocaleString('id-ID')}</div>
          <div className="text-[10px] text-muted-foreground">pcs dikirim</div>
        </GlassPanel>
      </div>

      {/* Flow Info Banner */}
      <GlassPanel className="p-3 flex items-start gap-3 border border-blue-400/20 bg-blue-400/5">
        <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
        <div className="text-xs text-muted-foreground leading-relaxed">
          <span className="font-semibold text-foreground">Alur Stok Produk Jadi:</span>
          <span className="mx-2 text-blue-300">Produksi Internal</span>
          WO selesai (bundle packed) → <b>FG +qty</b> → tetap di gudang sampai dikirim manual.
          <span className="mx-2 text-amber-300">Customer PO</span>
          WO selesai → <b>FG +qty</b> → Surat Jalan dispatch → <b>FG −qty</b>.
          Kode FG: <code className="text-primary font-mono">FG-[MODEL]-[SIZE]</code>
        </div>
      </GlassPanel>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="stock" data-testid="fg-tab-stock">
            <Package className="w-3.5 h-3.5 mr-1.5" /> Stok Saat Ini
          </TabsTrigger>
          <TabsTrigger value="movements" data-testid="fg-tab-movements">
            <Activity className="w-3.5 h-3.5 mr-1.5" /> Riwayat Pergerakan
          </TabsTrigger>
        </TabsList>

        {/* ── STOCK TAB ── */}
        <TabsContent value="stock">
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
              <span className="text-xs text-muted-foreground ml-auto">{items.length} SKU</span>
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
                  Otomatis muncul saat WO selesai (semua bundle packed) atau saat output Packing dicatat.
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
                            <span className={`text-lg font-bold ${qty > 0 ? 'text-emerald-400' : 'text-muted-foreground/50'}`}>
                              {qty.toLocaleString('id-ID')}
                            </span>
                            <span className="text-xs text-muted-foreground ml-1">pcs</span>
                          </td>
                          <td className="px-4 py-2.5 text-center">
                            {qty > 0 ? (
                              <Badge variant="outline" className="text-emerald-300 border-emerald-300/30 text-[10px]">
                                <TrendingUp className="w-3 h-3 mr-1" /> Ada Stok
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-muted-foreground text-[10px]">
                                <TrendingDown className="w-3 h-3 mr-1" /> Kosong
                              </Badge>
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
        </TabsContent>

        {/* ── MOVEMENTS TAB ── */}
        <TabsContent value="movements">
          <GlassCard className="p-0 overflow-hidden">
            {movements.length === 0 ? (
              <div className="text-center py-16 space-y-2">
                <Activity className="w-10 h-10 mx-auto text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">Belum ada pergerakan stok FG.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[11px] text-muted-foreground border-b border-[var(--glass-border)] bg-[var(--glass-bg)]">
                      <th className="px-4 py-2 text-left font-medium">Waktu</th>
                      <th className="px-4 py-2 text-left font-medium">Kode FG</th>
                      <th className="px-4 py-2 text-left font-medium">Arah</th>
                      <th className="px-4 py-2 text-right font-medium">Qty</th>
                      <th className="px-4 py-2 text-left font-medium">Sumber</th>
                      <th className="px-4 py-2 text-left font-medium">WO / Surat Jalan</th>
                      <th className="px-4 py-2 text-left font-medium">Keterangan</th>
                    </tr>
                  </thead>
                  <tbody>
                    {movements.map(mv => (
                      <tr key={mv.id} className="border-t border-[var(--glass-border)] hover:bg-[var(--glass-bg)]">
                        <td className="px-4 py-2 text-muted-foreground whitespace-nowrap">
                          {new Date(mv.timestamp).toLocaleString('id-ID', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' })}
                        </td>
                        <td className="px-4 py-2 font-mono text-xs text-emerald-300">{mv.fg_code}</td>
                        <td className="px-4 py-2">
                          {mv.direction === 'in' ? (
                            <span className="inline-flex items-center gap-1 text-emerald-300 font-medium">
                              <ArrowDownCircle className="w-3 h-3" /> Masuk
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-rose-300 font-medium">
                              <ArrowUpCircle className="w-3 h-3" /> Keluar
                            </span>
                          )}
                        </td>
                        <td className={`px-4 py-2 text-right font-bold ${mv.direction === 'in' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {mv.direction === 'in' ? '+' : '-'}{mv.qty} pcs
                        </td>
                        <td className="px-4 py-2">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                            mv.source === 'production_internal'
                              ? 'text-blue-300 border-blue-300/30 bg-blue-400/10'
                              : mv.source === 'production_customer_po'
                              ? 'text-amber-300 border-amber-300/30 bg-amber-400/10'
                              : mv.source === 'production_packing_event'
                              ? 'text-emerald-300 border-emerald-300/30 bg-emerald-400/10'
                              : 'text-rose-300 border-rose-300/30 bg-rose-400/10'
                          }`}>
                            {mv.source === 'production_internal'     ? 'Produksi Internal'
                            : mv.source === 'production_customer_po' ? 'Customer PO'
                            : mv.source === 'production_packing_event' ? 'Output Packing'
                            : mv.source === 'shipment_dispatch'      ? 'Surat Jalan'
                            : mv.source || 'Lainnya'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {mv.wo_number || mv.shipment_number || '—'}
                        </td>
                        <td className="px-4 py-2 text-muted-foreground truncate max-w-[160px]">
                          {mv.notes || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </TabsContent>
      </Tabs>
    </div>
  );
}
