# reactor_dashboard.py
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import datetime, timedelta
import time

class ReactorDashboard:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.setup_plots()
        
        # Dados históricos para tendências
        self.time_data = []
        self.temperature_data = []
        self.power_data = []
        self.rpm_data = []
        self.fuel_data = []
        self.efficiency_data = []
        
    def setup_plots(self):
        """Configura o dashboard com múltiplos gráficos"""
        plt.rcParams['figure.figsize'] = [15, 10]
        plt.rcParams['font.size'] = 8
        
        self.fig = plt.figure('Fusion Reactor Dashboard', facecolor='#1e1e1e')
        self.fig.suptitle('REATOR DE FUSÃO - MONITORAMENTO EM TEMPO REAL', 
                         color='white', fontsize=16, fontweight='bold')
        
        # Layout do dashboard
        gs = GridSpec(3, 3, figure=self.fig)
        
        # Gráficos principais
        self.temp_ax = self.fig.add_subplot(gs[0, 0])
        self.power_ax = self.fig.add_subplot(gs[0, 1])
        self.rpm_ax = self.fig.add_subplot(gs[0, 2])
        self.fuel_ax = self.fig.add_subplot(gs[1, 0])
        self.efficiency_ax = self.fig.add_subplot(gs[1, 1])
        self.alerts_ax = self.fig.add_subplot(gs[1, 2])
        self.trend_ax = self.fig.add_subplot(gs[2, :])
        
        self.style_plots()
        
    def style_plots(self):
        """Estiliza todos os gráficos"""
        axes = [self.temp_ax, self.power_ax, self.rpm_ax, 
                self.fuel_ax, self.efficiency_ax, self.alerts_ax, self.trend_ax]
        
        for ax in axes:
            ax.set_facecolor('#2b2b2b')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.title.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
    
    def update_dashboard(self, frame):
        """Atualiza todos os gráficos em tempo real"""
        analysis = self.analyzer.get_real_time_analysis()
        
        if analysis['status'] == 'offline':
            return
        
        current_time = datetime.now()
        
        # Atualiza dados históricos (mantém últimas 100 amostras)
        self.time_data.append(current_time)
        self.temperature_data.append(analysis['reactor']['temperatures']['plasma']['megakelvin'])
        self.power_data.append(analysis['turbine']['power']['power_watts'] / 1000)  # kW
        self.rpm_data.append(analysis['turbine']['rotation']['rpm'])
        self.fuel_data.append(analysis['reactor']['deuterium']['percentage'])
        
        if analysis['efficiency']:
            self.efficiency_data.append(analysis['efficiency'].get('overall_efficiency', 0))
        
        # Mantém apenas últimos 5 minutos de dados
        max_points = 300  # 5 minutos a 1Hz
        if len(self.time_data) > max_points:
            self.time_data = self.time_data[-max_points:]
            self.temperature_data = self.temperature_data[-max_points:]
            self.power_data = self.power_data[-max_points:]
            self.rpm_data = self.rpm_data[-max_points:]
            self.fuel_data = self.fuel_data[-max_points:]
            self.efficiency_data = self.efficiency_data[-max_points:]
        
        # Limpa todos os gráficos
        for ax in [self.temp_ax, self.power_ax, self.rpm_ax, 
                  self.fuel_ax, self.efficiency_ax, self.alerts_ax, self.trend_ax]:
            ax.clear()
            self.style_single_plot(ax)
        
        # Atualiza cada gráfico individualmente
        self.update_temperature_plot(analysis)
        self.update_power_plot(analysis)
        self.update_rpm_plot(analysis)
        self.update_fuel_plot(analysis)
        self.update_efficiency_plot(analysis)
        self.update_alerts_panel(analysis)
        self.update_trend_plot()
        
        plt.tight_layout()
    
    def style_single_plot(self, ax):
        """Estiliza um gráfico individual"""
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        ax.title.set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
    
    def update_temperature_plot(self, analysis):
        """Gráfico de temperatura do plasma"""
        reactor = analysis['reactor']
        temp_data = reactor['temperatures']['plasma']
        
        # Gráfico de gauge para temperatura
        current_temp = temp_data['megakelvin']
        max_safe_temp = 150  # MK
        
        self.temp_ax.set_xlim(0, 1)
        self.temp_ax.set_ylim(0, 1)
        
        # Cores baseadas na temperatura
        if current_temp > 120:
            color = 'red'
        elif current_temp > 80:
            color = 'orange'
        else:
            color = 'green'
        
        # Display estilo painel industrial
        self.temp_ax.text(0.5, 0.7, f'{current_temp:.1f}', ha='center', va='center', 
                         fontsize=24, color=color, fontweight='bold')
        self.temp_ax.text(0.5, 0.5, 'MEGAKELVIN', ha='center', va='center', 
                         fontsize=10, color='white')
        self.temp_ax.text(0.5, 0.3, f"{temp_data['celsius']:,.0f} °C", 
                         ha='center', va='center', fontsize=12, color='lightblue')
        
        # Barra de progresso
        progress = min(current_temp / max_safe_temp, 1.0)
        self.temp_ax.barh(0.1, progress, height=0.1, color=color, alpha=0.7)
        self.temp_ax.barh(0.1, 1-progress, height=0.1, left=progress, color='gray', alpha=0.3)
        
        self.temp_ax.set_title('TEMPERATURA DO PLASMA', fontweight='bold', pad=10)
        self.temp_ax.set_xticks([])
        self.temp_ax.set_yticks([])
    
    def update_power_plot(self, analysis):
        """Gráfico de produção de energia"""
        turbine = analysis['turbine']
        power_data = turbine['power']
        
        current_power = power_data['power_watts'] / 1000  # kW
        max_power = power_data['max_power_watts'] / 1000
        
        # Gráfico de pizza para carga atual
        labels = ['Produzindo', 'Capacidade Disponível']
        sizes = [current_power, max(0, max_power - current_power)]
        colors = ['#ff6b6b', '#4ecdc4']
        
        wedges, texts, autotexts = self.power_ax.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, textprops={'color': 'white'}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        self.power_ax.set_title(f'PRODUÇÃO DE ENERGIA\n{current_power:.0f} kW / {max_power:.0f} kW', 
                              fontweight='bold', pad=10)
    
    def update_rpm_plot(self, analysis):
        """Gráfico de rotação da turbina"""
        turbine = analysis['turbine']
        rotation_data = turbine['rotation']
        
        current_rpm = rotation_data['rpm']
        max_safe_rpm = 3600
        
        # Gráfico de velocímetro
        theta = np.linspace(0, np.pi, 100)
        r = np.ones(100)
        
        self.rpm_ax.plot(theta, r, color='white', linewidth=2)
        
        # Ponteiro
        rpm_ratio = min(current_rpm / max_safe_rpm, 1.0)
        pointer_angle = rpm_ratio * np.pi
        self.rpm_ax.plot([pointer_angle, pointer_angle], [0, 0.9], 
                        color='yellow', linewidth=3)
        
        # Zonas de cores
        safe_zone = np.linspace(0, 0.7 * np.pi, 50)
        warning_zone = np.linspace(0.7 * np.pi, 0.9 * np.pi, 20)
        danger_zone = np.linspace(0.9 * np.pi, np.pi, 30)
        
        self.rpm_ax.fill_between(safe_zone, 0, 1, color='green', alpha=0.3)
        self.rpm_ax.fill_between(warning_zone, 0, 1, color='orange', alpha=0.3)
        self.rpm_ax.fill_between(danger_zone, 0, 1, color='red', alpha=0.3)
        
        self.rpm_ax.text(np.pi/2, 0.5, f'{current_rpm:.0f}\nRPM', 
                        ha='center', va='center', fontsize=16, 
                        color='white', fontweight='bold')
        
        self.rpm_ax.set_title('ROTAÇÃO DA TURBINA', fontweight='bold', pad=10)
        self.rpm_ax.set_xlim(0, np.pi)
        self.rpm_ax.set_ylim(0, 1)
        self.rpm_ax.set_xticks([])
        self.rpm_ax.set_yticks([])
    
    def update_fuel_plot(self, analysis):
        """Gráfico de nível de combustível"""
        reactor = analysis['reactor']
        fuel_data = reactor['deuterium']
        
        current_fuel = fuel_data['percentage']
        
        # Gráfico de barras vertical estilo tanque
        self.fuel_ax.bar(0, current_fuel, width=0.6, color='cyan', alpha=0.7, label='Atual')
        self.fuel_ax.bar(0, 100-current_fuel, width=0.6, bottom=current_fuel, 
                        color='gray', alpha=0.3, label='Vazio')
        
        # Linhas de referência
        for level in [20, 50, 80]:
            self.fuel_ax.axhline(level, color='white', linestyle='--', alpha=0.5)
            self.fuel_ax.text(0.3, level, f'{level}%', va='center', color='white')
        
        self.fuel_ax.text(0, current_fuel + 5, f'{current_fuel:.1f}%', 
                         ha='center', color='white', fontweight='bold', fontsize=12)
        
        self.fuel_ax.set_ylim(0, 100)
        self.fuel_ax.set_xlim(-0.5, 0.5)
        self.fuel_ax.set_xticks([])
        self.fuel_ax.set_ylabel('Nível de Combustível (%)', color='white')
        self.fuel_ax.set_title('RESERVA DE DEUTÉRIO', fontweight='bold', pad=10)
    
    def update_efficiency_plot(self, analysis):
        """Gráfico de eficiência do sistema"""
        efficiency_data = analysis['efficiency']
        
        metrics = []
        values = []
        colors = []
        
        if efficiency_data:
            if 'thermal_efficiency' in efficiency_data:
                metrics.append('Térmica')
                values.append(efficiency_data['thermal_efficiency'])
                colors.append('#ff9ff3')
            
            if 'steam_cycle_efficiency' in efficiency_data:
                metrics.append('Ciclo Vapor')
                values.append(efficiency_data['steam_cycle_efficiency'])
                colors.append('#74b9ff')
            
            if 'overall_efficiency' in efficiency_data:
                metrics.append('Global')
                values.append(efficiency_data['overall_efficiency'])
                colors.append('#00b894')
        
        if values:
            bars = self.efficiency_ax.bar(metrics, values, color=colors, alpha=0.7)
            
            # Adiciona valores nas barras
            for bar, value in zip(bars, values):
                height = bar.get_height()
                self.efficiency_ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                                       f'{value:.1f}%', ha='center', va='bottom', 
                                       color='white', fontweight='bold')
            
            self.efficiency_ax.set_ylim(0, 100)
            self.efficiency_ax.set_ylabel('Eficiência (%)', color='white')
        
        self.efficiency_ax.set_title('EFICIÊNCIA DO SISTEMA', fontweight='bold', pad=10)
    
    def update_alerts_panel(self, analysis):
        """Painel de alertas e status"""
        self.alerts_ax.set_xlim(0, 1)
        self.alerts_ax.set_ylim(0, 1)
        
        status_color = 'green' if analysis['status'] == 'NORMAL' else 'red'
        
        # Status principal
        self.alerts_ax.text(0.5, 0.9, analysis['status'], ha='center', va='center',
                          fontsize=16, color=status_color, fontweight='bold',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor=status_color, alpha=0.2))
        
        # Alertas
        y_pos = 0.7
        if analysis['anomalies']:
            self.alerts_ax.text(0.1, y_pos, '🚨 ALERTAS ATIVOS:', 
                              color='red', fontweight='bold', fontsize=10)
            y_pos -= 0.1
            
            for alert in analysis['anomalies'][:3]:  # Mostra até 3 alertas
                self.alerts_ax.text(0.1, y_pos, f'• {alert}', 
                                  color='orange', fontsize=8, wrap=True)
                y_pos -= 0.08
        else:
            self.alerts_ax.text(0.5, 0.5, '✅ TODOS OS SISTEMAS\n   OPERACIONAIS', 
                              ha='center', va='center', color='green', fontweight='bold')
        
        # Métricas rápidas
        reactor = analysis['reactor']
        y_pos = 0.3
        quick_metrics = [
            f"Injeção: {reactor['injection']['kg_per_second']:.1f} kg/s",
            f"Vapor: {reactor['steam_production']['kg_per_second']:.1f} kg/s",
            f"Pressão: {reactor['steam_storage']['pressure_bar']:.1f} bar"
        ]
        
        for metric in quick_metrics:
            self.alerts_ax.text(0.1, y_pos, metric, color='lightblue', fontsize=8)
            y_pos -= 0.06
        
        self.alerts_ax.set_title('STATUS E ALERTAS', fontweight='bold', pad=10)
        self.alerts_ax.set_xticks([])
        self.alerts_ax.set_yticks([])
    
    def update_trend_plot(self):
        """Gráfico de tendências temporais"""
        if len(self.time_data) < 2:
            return
        
        # Converte tempos para minutos relativos
        time_deltas = [(t - self.time_data[0]).total_seconds() / 60 for t in self.time_data]
        
        # Plota múltiplas tendências
        self.trend_ax.plot(time_deltas, self.temperature_data, 'r-', label='Temp (MK)', linewidth=2)
        self.trend_ax.plot(time_deltas, [p/100 for p in self.power_data], 'y-', 
                          label='Potência (kW/100)', linewidth=2)
        self.trend_ax.plot(time_deltas, [r/50 for r in self.rpm_data], 'c-', 
                          label='RPM/50', linewidth=2)
        self.trend_ax.plot(time_deltas, self.fuel_data, 'g-', label='Combustível (%)', linewidth=2)
        
        self.trend_ax.set_xlabel('Tempo (minutos)', color='white')
        self.trend_ax.set_ylabel('Valores Normalizados', color='white')
        self.trend_ax.legend(loc='upper right', facecolor='#2b2b2b', edgecolor='white')
        self.trend_ax.set_title('TENDÊNCIAS TEMPORAIS (Últimos 5min)', fontweight='bold', pad=10)
        self.trend_ax.grid(True, alpha=0.3)
    
    def start_dashboard(self):
        """Inicia o dashboard animado"""
        print("Iniciando dashboard em tempo real...")
        print("Feche a janela para parar")
        
        # Animação que atualiza a cada segundo
        ani = animation.FuncAnimation(
            self.fig, self.update_dashboard, interval=1000, cache_frame_data=False
        )
        
        plt.show()

# Uso completo
if __name__ == "__main__":
    from fusion_analyzer import ReactorDataProcessor
    
    analyzer = ReactorDataProcessor()
    dashboard = ReactorDashboard(analyzer)
    dashboard.start_dashboard()