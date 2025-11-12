# fusion_monitor_advanced.py
import tkinter as tk
from tkinter import ttk
import json
import threading
import time
from datetime import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib import style

# Configurar estilo dos gráficos
style.use('dark_background')
plt.rcParams['axes.facecolor'] = '#1e1e1e'
plt.rcParams['figure.facecolor'] = '#2d2d2d'

class FusionMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("🏭 Fusion Reactor Monitor - Advanced")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Dados históricos para gráficos
        self.time_data = []
        self.plasma_temp_data = []
        self.case_temp_data = []
        self.injection_rate_data = []
        self.energy_production_data = []
        self.max_history = 100  # Pontos máximos no gráfico
        
        # Configurar interface
        self.setup_ui()
        
        # Iniciar thread de atualização
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
    def setup_ui(self):
        # Configurar estilo
        self.setup_styles()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15", style='Dark.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self.setup_header(main_frame)
        
        # Painel de Métricas em Tempo Real
        self.setup_metrics_panel(main_frame)
        
        # Painel de Gráficos
        self.setup_graphs_panel(main_frame)
        
    def setup_styles(self):
        """Configura os estilos visuais"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar cores
        style.configure('Dark.TFrame', background='#1e1e1e')
        style.configure('Dark.TLabelframe', background='#2d2d2d', foreground='white')
        style.configure('Dark.TLabelframe.Label', background='#2d2d2d', foreground='white')
        style.configure('Title.TLabel', background='#1e1e1e', foreground='#00ff88', font=('Arial', 18, 'bold'))
        style.configure('Subtitle.TLabel', background='#1e1e1e', foreground='#cccccc', font=('Arial', 12))
        style.configure('Metric.TLabel', background='#2d2d2d', foreground='white', font=('Arial', 10))
        style.configure('Value.TLabel', background='#2d2d2d', foreground='#00ff88', font=('Arial', 12, 'bold'))
        style.configure('Unit.TLabel', background='#2d2d2d', foreground='#888888', font=('Arial', 9))
        
    def setup_header(self, parent):
        """Configura o cabeçalho"""
        header_frame = ttk.Frame(parent, style='Dark.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Título principal
        title_label = ttk.Label(header_frame, text="🏭 FUSION REACTOR MONITOR", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Subtítulo
        subtitle_label = ttk.Label(header_frame, text="Monitoramento em Tempo Real - Minecraft Fusion Reactor", 
                                 style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Status e timestamp
        self.status_label = ttk.Label(header_frame, text="● Status: Aguardando dados...", 
                                    style='Subtitle.TLabel', foreground='orange')
        self.status_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        self.timestamp_label = ttk.Label(header_frame, text="Última atualização: --", 
                                       style='Subtitle.TLabel', foreground='#888888')
        self.timestamp_label.grid(row=3, column=0, sticky=tk.W, pady=(2, 0))
        
    def setup_metrics_panel(self, parent):
        """Configura o painel de métricas em tempo real"""
        metrics_frame = ttk.Frame(parent, style='Dark.TFrame')
        metrics_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Frame do Reator
        reactor_frame = ttk.LabelFrame(metrics_frame, text="🔬 REATOR DE FUSÃO", padding="15", style='Dark.TLabelframe')
        reactor_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        reactor_frame.columnconfigure(1, weight=1)
        
        # Dados do Reator (apenas temperaturas e taxa de injeção)
        self.setup_reactor_widgets(reactor_frame)
        
        # Frame da Turbina
        turbine_frame = ttk.LabelFrame(metrics_frame, text="⚡ TURBINA", padding="15", style='Dark.TLabelframe')
        turbine_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        turbine_frame.columnconfigure(1, weight=1)
        
        # Dados da Turbina
        self.setup_turbine_widgets(turbine_frame)
        
        metrics_frame.rowconfigure(0, weight=1)
        metrics_frame.rowconfigure(1, weight=1)
        
    def setup_reactor_widgets(self, parent):
        """Configura os widgets para dados do reator"""
        row = 0
        
        # Temperatura do Plasma
        ttk.Label(parent, text="Temperatura do Plasma:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.plasma_temp_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.plasma_temp_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="°C", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Temperatura do Casco
        ttk.Label(parent, text="Temperatura do Casco:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.case_temp_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.case_temp_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="°C", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Taxa de Injeção
        ttk.Label(parent, text="Taxa de Injeção:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.injection_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.injection_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="mB/t", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Barra de status do reator
        self.reactor_status_var = tk.StringVar(value="Reator: Aguardando dados")
        ttk.Label(parent, textvariable=self.reactor_status_var, style='Metric.TLabel', 
                 foreground='orange').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 0))
        row += 1
        
    def setup_turbine_widgets(self, parent):
        """Configura os widgets para dados da turbina"""
        row = 0
        
        # Produção de Energia
        ttk.Label(parent, text="Produção de Energia:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.production_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.production_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="J/t", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Produção Máxima
        ttk.Label(parent, text="Capacidade Máxima:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.max_production_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.max_production_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="J/t", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Eficiência
        ttk.Label(parent, text="Eficiência:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.efficiency_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.efficiency_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="%", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Vazão de Steam
        ttk.Label(parent, text="Vazão de Steam:", style='Metric.TLabel').grid(row=row, column=0, sticky=tk.W, pady=8)
        self.flow_var = tk.StringVar(value="--")
        ttk.Label(parent, textvariable=self.flow_var, style='Value.TLabel').grid(row=row, column=1, sticky=tk.W, pady=8)
        ttk.Label(parent, text="mB/t", style='Unit.TLabel').grid(row=row, column=2, sticky=tk.W, pady=8, padx=(5, 0))
        row += 1
        
        # Barra de status da turbina
        self.turbine_status_var = tk.StringVar(value="Turbina: Aguardando dados")
        ttk.Label(parent, textvariable=self.turbine_status_var, style='Metric.TLabel', 
                 foreground='orange').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 0))
        row += 1
        
    def setup_graphs_panel(self, parent):
        """Configura o painel de gráficos"""
        graphs_frame = ttk.Frame(parent, style='Dark.TFrame')
        graphs_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        graphs_frame.columnconfigure(0, weight=1)
        graphs_frame.rowconfigure(0, weight=1)
        graphs_frame.rowconfigure(1, weight=1)
        
        # Gráfico de Temperaturas
        self.setup_temperature_graph(graphs_frame)
        
        # Gráfico de Energia
        self.setup_energy_graph(graphs_frame)
        
    def setup_temperature_graph(self, parent):
        """Configura o gráfico de temperaturas"""
        temp_frame = ttk.LabelFrame(parent, text="📊 TEMPERATURAS DO REATOR", padding="10", style='Dark.TLabelframe')
        temp_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.rowconfigure(0, weight=1)
        
        # Criar figura do matplotlib
        self.temp_fig, self.temp_ax = plt.subplots(figsize=(6, 3), facecolor='#2d2d2d')
        self.temp_ax.set_facecolor('#1e1e1e')
        
        # Configurar gráfico
        self.temp_ax.set_title('Temperaturas ao Longo do Tempo', color='white', pad=10)
        self.temp_ax.set_ylabel('Temperatura (°C)', color='white')
        self.temp_ax.set_xlabel('Tempo (segundos)', color='white')
        self.temp_ax.tick_params(colors='white')
        self.temp_ax.grid(True, alpha=0.3)
        
        # Inicializar linhas
        self.plasma_line, = self.temp_ax.plot([], [], label='Plasma', color='#ff4444', linewidth=2)
        self.case_line, = self.temp_ax.plot([], [], label='Casco', color='#44aaff', linewidth=2)
        self.temp_ax.legend(facecolor='#2d2d2d', edgecolor='#444444', labelcolor='white')
        
        # Embed no tkinter
        self.temp_canvas = FigureCanvasTkAgg(self.temp_fig, temp_frame)
        self.temp_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def setup_energy_graph(self, parent):
        """Configura o gráfico de energia"""
        energy_frame = ttk.LabelFrame(parent, text="⚡ PRODUÇÃO DE ENERGIA", padding="10", style='Dark.TLabelframe')
        energy_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        energy_frame.columnconfigure(0, weight=1)
        energy_frame.rowconfigure(0, weight=1)
        
        # Criar figura do matplotlib
        self.energy_fig, self.energy_ax = plt.subplots(figsize=(6, 3), facecolor='#2d2d2d')
        self.energy_ax.set_facecolor('#1e1e1e')
        
        # Configurar gráfico
        self.energy_ax.set_title('Produção de Energia da Turbina', color='white', pad=10)
        self.energy_ax.set_ylabel('Energia (J/t)', color='white')
        self.energy_ax.set_xlabel('Tempo (segundos)', color='white')
        self.energy_ax.tick_params(colors='white')
        self.energy_ax.grid(True, alpha=0.3)
        
        # Inicializar linha
        self.energy_line, = self.energy_ax.plot([], [], label='Produção', color='#00ff88', linewidth=2)
        self.energy_ax.legend(facecolor='#2d2d2d', edgecolor='#444444', labelcolor='white')
        
        # Embed no tkinter
        self.energy_canvas = FigureCanvasTkAgg(self.energy_fig, energy_frame)
        self.energy_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def update_loop(self):
        """Loop principal de atualização dos dados"""
        start_time = time.time()
        
        while self.running:
            try:
                current_time = time.time() - start_time
                
                if os.path.exists("fusion_data.json"):
                    with open("fusion_data.json", 'r') as f:
                        new_data = json.load(f)
                    
                    # Atualiza interface na thread principal
                    self.root.after(0, self.update_interface, new_data, current_time)
                
                time.sleep(0.5)  # Atualiza a cada 0.5 segundos
                
            except Exception as e:
                print(f"Erro no loop de atualização: {e}")
                time.sleep(2)
                
    def update_interface(self, data, current_time):
        """Atualiza a interface com novos dados"""
        # Atualizar header
        self.timestamp_label.config(text=f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")
        status = data.get('status', 'aguardando_dados')
        status_color = '#00ff88' if status == 'ativo' else 'orange'
        self.status_label.config(text=f"● Status: {status.upper()}", foreground=status_color)
        
        # Dados do Reator
        reactor_data = data.get('reactor', {})
        self.update_reactor_display(reactor_data, current_time)
        
        # Dados da Turbina
        turbine_data = data.get('turbine', {})
        self.update_turbine_display(turbine_data, current_time)
        
        # Atualizar gráficos
        self.update_graphs(current_time)
        
    def update_reactor_display(self, reactor_data, current_time):
        """Atualiza a exibição dos dados do reator"""
        if reactor_data:
            # Temperaturas (já em Celsius)
            plasma_temp = reactor_data.get('plasma_temperature', 0)
            case_temp = reactor_data.get('case_temperature', 0)
            
            self.plasma_temp_var.set(f"{plasma_temp:,.0f}")
            self.case_temp_var.set(f"{case_temp:,.0f}")
            
            # Taxa de injeção (mB/tick - mantém a unidade do Minecraft)
            injection_rate = reactor_data.get('injection_rate', 0)
            self.injection_var.set(f"{injection_rate:,.0f}")
            
            # Status do reator
            if plasma_temp > 1e8:
                status_text = "⚠️  ALERTA: Temperatura crítica!"
                status_color = '#ff4444'
            elif plasma_temp > 5e7:
                status_text = "⚠️  AVISO: Temperatura alta"
                status_color = 'orange'
            else:
                status_text = "✅ Reator operando normalmente"
                status_color = '#00ff88'
            
            self.reactor_status_var.set(status_text)
            # Não é possível alterar cor do texto dinamicamente no ttk, então usamos foreground fixo
            
            # Adicionar dados históricos
            self.time_data.append(current_time)
            self.plasma_temp_data.append(plasma_temp)
            self.case_temp_data.append(case_temp)
            self.injection_rate_data.append(injection_rate)
            
            # Limitar histórico
            if len(self.time_data) > self.max_history:
                self.time_data.pop(0)
                self.plasma_temp_data.pop(0)
                self.case_temp_data.pop(0)
                self.injection_rate_data.pop(0)
        
    def update_turbine_display(self, turbine_data, current_time):
        """Atualiza a exibição dos dados da turbina"""
        if turbine_data:
            # Converter RF/t para J/t (1 RF = 10 J no contexto do mod)
            production_rf = turbine_data.get('production_rate', 0)
            max_production_rf = turbine_data.get('max_production', 0)
            
            production_j = production_rf * 10  # Conversão para Joules
            max_production_j = max_production_rf * 10  # Conversão para Joules
            
            self.production_var.set(f"{production_j:,.0f}")
            self.max_production_var.set(f"{max_production_j:,.0f}")
            
            # Eficiência
            if max_production_j > 0:
                efficiency = (production_j / max_production_j) * 100
                self.efficiency_var.set(f"{efficiency:.1f}")
            else:
                self.efficiency_var.set("0.0")
            
            # Vazão (mB/tick - mantém unidade do Minecraft)
            flow_rate = turbine_data.get('flow_rate', 0)
            self.flow_var.set(f"{flow_rate:,.0f}")
            
            # Status da turbina
            if efficiency >= 90:
                status_text = "✅ Turbina em capacidade máxima"
                status_color = '#00ff88'
            elif efficiency >= 50:
                status_text = "⚡ Turbina operando eficientemente"
                status_color = '#44aaff'
            else:
                status_text = "⚠️  Turbina em baixa eficiência"
                status_color = 'orange'
            
            self.turbine_status_var.set(status_text)
            
            # Adicionar dados históricos de energia
            self.energy_production_data.append(production_j)
            if len(self.energy_production_data) > self.max_history:
                self.energy_production_data.pop(0)
        
    def update_graphs(self, current_time):
        """Atualiza os gráficos"""
        if len(self.time_data) > 0:
            # Atualizar gráfico de temperaturas
            self.plasma_line.set_data(self.time_data, self.plasma_temp_data)
            self.case_line.set_data(self.time_data, self.case_temp_data)
            
            self.temp_ax.relim()
            self.temp_ax.autoscale_view()
            self.temp_canvas.draw()
            
            # Atualizar gráfico de energia
            self.energy_line.set_data(self.time_data, self.energy_production_data)
            
            self.energy_ax.relim()
            self.energy_ax.autoscale_view()
            self.energy_canvas.draw()
            
    def on_closing(self):
        """Executado quando a janela é fechada"""
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FusionMonitor(root)
    
    # Configurar fechamento seguro
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    print("🚀 Fusion Monitor Avançado iniciado!")
    print("📊 Monitorando fusion_data.json em tempo real...")
    print("📈 Gráficos ativos - Interface dark mode")
    print("-" * 50)
    
    root.mainloop()

if __name__ == "__main__":
    main()