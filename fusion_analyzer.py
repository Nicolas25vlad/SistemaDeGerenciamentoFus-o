# fusion_analyzer.py
import requests
import time
from datetime import datetime
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class RealWorldConstants:
    """Constantes para conversão para unidades reais"""
    BUCKET_TO_LITERS = 1000.0
    TICK_TO_SECONDS = 1/20.0
    FE_TO_JOULES = 2.5
    STEAM_DENSITY = 0.6  # kg/L (vapor saturado)
    WATER_DENSITY = 1.0  # kg/L
    RPM_BASE = 1800
    CELSIUS_TO_KELVIN = 273.15

class ReactorDataProcessor:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.constants = RealWorldConstants()
        self.data_history = deque(maxlen=600)  # 10 minutos de dados
    
    def fetch_raw_data(self) -> Optional[Dict]:
        """Busca dados brutos do Lua"""
        try:
            response = requests.get(f"{self.base_url}/api/raw", timeout=2)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Erro ao buscar dados: {e}")
            return None
    
    def process_reactor_data(self, raw_reactor: Dict) -> Dict:
        """Processa dados brutos do reator para unidades reais"""
        processed = {
            'timestamp': datetime.now(),
            'status': 'online',
            'raw_data': raw_reactor
        }
        
        # COMBUSTÍVEL (Deutério)
        if raw_reactor.get('deuterium'):
            deuterium = raw_reactor['deuterium']
            capacity = raw_reactor.get('deuterium_capacity', 1)
            
            # Extrai amount do objeto deuterium (pode ser um dict ou objeto)
            amount = deuterium.get('amount', 0) if isinstance(deuterium, dict) else getattr(deuterium, 'amount', 0)
            
            processed['deuterium'] = {
                'amount_ml': amount,
                'capacity_ml': capacity,
                'amount_liters': (amount / 1000) * self.constants.BUCKET_TO_LITERS,
                'capacity_liters': capacity / 1000 * self.constants.BUCKET_TO_LITERS,
                'percentage': (amount / capacity * 100) if capacity > 0 else 0
            }
        
        # TAXA DE INJEÇÃO (L/s)
        injection_rate = raw_reactor.get('injection_rate', 0)
        processed['injection'] = {
            'mb_per_tick': injection_rate,
            'liters_per_second': (injection_rate / 1000) * self.constants.BUCKET_TO_LITERS / self.constants.TICK_TO_SECONDS,
            'kg_per_second': (injection_rate / 1000) * self.constants.WATER_DENSITY / self.constants.TICK_TO_SECONDS
        }
        
        # TEMPERATURAS
        plasma_temp = raw_reactor.get('plasma_temperature', 0)
        max_plasma_temp = raw_reactor.get('max_plasma_temperature', 1)
        
        processed['temperatures'] = {
            'plasma': {
                'celsius': plasma_temp,
                'kelvin': plasma_temp + self.constants.CELSIUS_TO_KELVIN,
                'megakelvin': (plasma_temp + self.constants.CELSIUS_TO_KELVIN) / 1e6,
                'percentage': (plasma_temp / max_plasma_temp * 100) if max_plasma_temp > 0 else 0
            },
            'case': {
                'celsius': raw_reactor.get('case_temperature', 0),
                'kelvin': raw_reactor.get('case_temperature', 0) + self.constants.CELSIUS_TO_KELVIN
            }
        }
        
        # ÁGUA
        if raw_reactor.get('water'):
            water = raw_reactor['water']
            water_capacity = raw_reactor.get('water_capacity', 1)
            water_amount = water.get('amount', 0) if isinstance(water, dict) else getattr(water, 'amount', 0)
            
            processed['water'] = {
                'amount_liters': (water_amount / 1000) * self.constants.BUCKET_TO_LITERS,
                'capacity_liters': water_capacity / 1000 * self.constants.BUCKET_TO_LITERS,
                'percentage': (water_amount / water_capacity * 100) if water_capacity > 0 else 0
            }
        
        # PRODUÇÃO DE VAPOR
        production_rate = raw_reactor.get('production_rate', 0)
        processed['steam_production'] = {
            'mb_per_tick': production_rate,
            'liters_per_second': (production_rate / 1000) * self.constants.BUCKET_TO_LITERS / self.constants.TICK_TO_SECONDS,
            'kg_per_second': (production_rate / 1000) * self.constants.STEAM_DENSITY / self.constants.TICK_TO_SECONDS
        }
        
        # VAPOR ARMAZENADO
        if raw_reactor.get('steam'):
            steam = raw_reactor['steam']
            steam_capacity = raw_reactor.get('steam_capacity', 1)
            steam_amount = steam.get('amount', 0) if isinstance(steam, dict) else getattr(steam, 'amount', 0)
            
            processed['steam_storage'] = {
                'amount_liters': (steam_amount / 1000) * self.constants.BUCKET_TO_LITERS,
                'capacity_liters': steam_capacity / 1000 * self.constants.BUCKET_TO_LITERS,
                'percentage': (steam_amount / steam_capacity * 100) if steam_capacity > 0 else 0,
                'pressure_bar': (steam_amount / steam_capacity * 50) if steam_capacity > 0 else 0
            }
        
        # ENERGIA
        energy = raw_reactor.get('energy', 0)
        max_energy = raw_reactor.get('max_energy', 1)
        
        processed['energy'] = {
            'stored_fe': energy,
            'capacity_fe': max_energy,
            'stored_joules': energy * self.constants.FE_TO_JOULES,
            'capacity_joules': max_energy * self.constants.FE_TO_JOULES,
            'percentage': (energy / max_energy * 100) if max_energy > 0 else 0
        }
        
        return processed
    
    def process_turbine_data(self, raw_turbine: Dict) -> Dict:
        """Processa dados brutos da turbina para unidades reais"""
        processed = {
            'timestamp': datetime.now(),
            'status': 'online'
        }
        
        # ROTAÇÃO (RPM)
        flow_rate = raw_turbine.get('flow_rate', 0)
        max_flow_rate = raw_turbine.get('max_flow_rate', 1)
        efficiency = flow_rate / max_flow_rate if max_flow_rate > 0 else 0
        
        processed['rotation'] = {
            'flow_rate_mb': flow_rate,
            'max_flow_rate_mb': max_flow_rate,
            'efficiency': efficiency,
            'rpm': efficiency * self.constants.RPM_BASE * 2,
            'angular_velocity_rad_s': efficiency * self.constants.RPM_BASE * 2 * (2 * np.pi / 60)
        }
        
        # PRODUÇÃO DE ENERGIA (Watts)
        production = raw_turbine.get('production_rate', 0)
        max_production = raw_turbine.get('max_production', 1)
        
        processed['power'] = {
            'fe_per_tick': production,
            'max_fe_per_tick': max_production,
            'power_watts': (production * self.constants.FE_TO_JOULES) / self.constants.TICK_TO_SECONDS,
            'max_power_watts': (max_production * self.constants.FE_TO_JOULES) / self.constants.TICK_TO_SECONDS,
            'efficiency': production / max_production if max_production > 0 else 0
        }
        
        # ENERGIA ARMAZENADA
        energy = raw_turbine.get('energy', 0)
        max_energy = raw_turbine.get('max_energy', 1)
        
        processed['energy_storage'] = {
            'stored_joules': energy * self.constants.FE_TO_JOULES,
            'capacity_joules': max_energy * self.constants.FE_TO_JOULES,
            'percentage': (energy / max_energy * 100) if max_energy > 0 else 0
        }
        
        # CONSUMO DE VAPOR
        if raw_turbine.get('steam'):
            steam = raw_turbine['steam']
            steam_capacity = raw_turbine.get('steam_capacity', 1)
            steam_amount = steam.get('amount', 0) if isinstance(steam, dict) else getattr(steam, 'amount', 0)
            
            steam_kg = (steam_amount / 1000) * self.constants.STEAM_DENSITY
            power_w = processed['power']['power_watts']
            
            processed['steam_consumption'] = {
                'amount_kg': steam_kg,
                'capacity_kg': steam_capacity / 1000 * self.constants.STEAM_DENSITY,
                'specific_consumption': power_w / steam_kg if steam_kg > 0 else 0,
                'efficiency_rankine': min(100, (power_w / (steam_kg * 2500)) * 100) if steam_kg > 0 else 0
            }
        
        return processed
    
    def calculate_efficiency_metrics(self, reactor_data: Dict, turbine_data: Dict) -> Dict:
        """Calcula métricas de eficiência do sistema completo"""
        metrics = {}
        
        # Eficiência térmica
        if (reactor_data.get('deuterium') and turbine_data.get('power')):
            deuterium_liters = reactor_data['deuterium']['amount_liters']
            power_w = turbine_data['power']['power_watts']
            
            # Energia teórica do deutério (aproximação)
            theoretical_energy = deuterium_liters * 8.6e10
            metrics['thermal_efficiency'] = (power_w / theoretical_energy * 100) if theoretical_energy > 0 else 0
        
        # Eficiência do ciclo vapor
        if (reactor_data.get('steam_production') and turbine_data.get('power')):
            steam_kg_s = reactor_data['steam_production']['kg_per_second']
            power_kw = turbine_data['power']['power_watts'] / 1000
            
            thermal_power = steam_kg_s * 2800  # kJ/kg
            metrics['steam_cycle_efficiency'] = (power_kw / thermal_power * 100) if thermal_power > 0 else 0
        
        # Eficiência global
        if metrics.get('thermal_efficiency') and metrics.get('steam_cycle_efficiency'):
            metrics['overall_efficiency'] = (metrics['thermal_efficiency'] * metrics['steam_cycle_efficiency']) / 100
        
        return metrics
    
    def detect_anomalies(self, reactor_data: Dict, turbine_data: Dict) -> list:
        """Detecta anomalias operacionais"""
        anomalies = []
        
        # Limites operacionais
        limits = {
            'max_plasma_temp_k': 2e8,    # 200 milhões K
            'max_case_temp_k': 1500,     # 1500 K
            'max_rpm': 3600,             # 3600 RPM
            'min_deuterium': 5,          # 5%
            'temp_gradient': 1e8         # 100 milhões K
        }
        
        # Verificações de segurança
        plasma_temp = reactor_data['temperatures']['plasma']['kelvin']
        if plasma_temp > limits['max_plasma_temp_k']:
            anomalies.append(f"Temperatura do plasma crítica: {plasma_temp:.2e} K")
        
        case_temp = reactor_data['temperatures']['case']['kelvin']
        if case_temp > limits['max_case_temp_k']:
            anomalies.append(f"Temperatura do casco alta: {case_temp:.0f} K")
        
        rpm = turbine_data['rotation']['rpm']
        if rpm > limits['max_rpm']:
            anomalies.append(f"Rotação excessiva: {rpm:.0f} RPM")
        
        deuterium_pct = reactor_data['deuterium']['percentage']
        if deuterium_pct < limits['min_deuterium']:
            anomalies.append(f"Combustível crítico: {deuterium_pct:.1f}%")
        
        temp_gradient = plasma_temp - case_temp
        if temp_gradient > limits['temp_gradient']:
            anomalies.append(f"Gradiente térmico excessivo: {temp_gradient:.2e} K")
        
        return anomalies
    
    def get_real_time_analysis(self) -> Dict:
        """Análise completa em tempo real"""
        raw_data = self.fetch_raw_data()
        if not raw_data:
            return {'status': 'offline', 'error': 'No data available'}
        
        # Processa dados brutos
        reactor_processed = self.process_reactor_data(raw_data.get('reactor', {}))
        turbine_processed = self.process_turbine_data(raw_data.get('turbine', {}))
        
        # Calcula métricas avançadas
        efficiency = self.calculate_efficiency_metrics(reactor_processed, turbine_processed)
        anomalies = self.detect_anomalies(reactor_processed, turbine_processed)
        
        # Resultado final
        analysis_result = {
            'timestamp': datetime.now(),
            'status': 'CRITICAL' if anomalies else 'NORMAL',
            'reactor': reactor_processed,
            'turbine': turbine_processed,
            'efficiency': efficiency,
            'anomalies': anomalies
        }
        
        # Armazena no histórico
        self.data_history.append(analysis_result)
        
        return analysis_result

# Teste simples
if __name__ == "__main__":
    analyzer = ReactorDataProcessor()
    
    print("Testando Fusion Analyzer...")
    analysis = analyzer.get_real_time_analysis()
    
    if analysis['status'] != 'offline':
        print("✅ Analyzer funcionando!")
        print(f"Status: {analysis['status']}")
        print(f"Temperatura: {analysis['reactor']['temperatures']['plasma']['megakelvin']:.1f} MK")
        print(f"Potência: {analysis['turbine']['power']['power_watts']/1000:.1f} kW")
    else:
        print("❌ Analyzer offline - verifique o script Lua")