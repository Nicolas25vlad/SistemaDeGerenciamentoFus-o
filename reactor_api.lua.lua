-- fusion_client.lua

local Config = {
    SERVER_IP = "",  -- ALTERE PARA SEU IP
    SERVER_PORT = 8765,
    UPDATE_INTERVAL = 2,  -- segundos
    WEBSOCKET_URL = nil  -- Será preenchido automaticamente
}

Config.WEBSOCKET_URL = "ws://" .. Config.SERVER_IP .. ":" .. Config.SERVER_PORT

local websocket = nil
local dadosReator = {}
local dadosTurbina = {}
local analiseRecebida = {}

-- Funções de comunicação com WebSocket
local function conectarServidor()
    print("🔗 Conectando ao servidor Fusion...")
    print("URL: " .. Config.WEBSOCKET_URL)
    
    local ok, ws = pcall(function()
        return http.websocket(Config.WEBSOCKET_URL)
    end)
    
    if ok and ws then
        print("✅ Conectado ao servidor!")
        websocket = ws
        
        -- Escuta mensagem de boas-vindas
        local mensagem = ws.receive(1)
        if mensagem then
            local dados = textutils.unserializeJSON(mensagem)
            if dados and dados.tipo == "conexao" then
                print("📨 " .. dados.mensagem)
            end
        end
        
        return true
    else
        print("❌ Falha na conexão: " .. tostring(ws))
        websocket = nil
        return false
    end
end

local function enviarMensagem(tipo, dados)
    if not websocket then
        return false
    end
    
    local mensagem = {
        tipo = tipo,
        timestamp = os.epoch("utc"),
        dados = dados or {}
    }
    
    local json_msg = textutils.serializeJSON(mensagem)
    return websocket.send(json_msg)
end

local function receberMensagem(timeout)
    if not websocket then
        return nil
    end
    
    local mensagem = websocket.receive(timeout or 1)
    if mensagem then
        return textutils.unserializeJSON(mensagem)
    end
    return nil
end

-- Funções de coleta de dados das peripherals
local function coletarDadosReator()
    local dados = {}
    local perifericos = peripheral.getNames()
    
    for _, nome in ipairs(perifericos) do
        local tipo = peripheral.getType(nome)
        if tipo == "fusionReactorLogicAdapter" then
            local reactor = peripheral.wrap(nome)
            
            -- Coleta todos os dados disponíveis do reator
            if reactor.getDeuterium then dados.deuterium = reactor.getDeuterium() end
            if reactor.getDeuteriumCapacity then dados.deuterium_capacity = reactor.getDeuteriumCapacity() end
            if reactor.getInjectionRate then dados.injection_rate = reactor.getInjectionRate() end
            if reactor.getPlasmaTemperature then dados.plasma_temperature = reactor.getPlasmaTemperature() end
            if reactor.getCaseTemperature then dados.case_temperature = reactor.getCaseTemperature() end
            if reactor.getWater then dados.water = reactor.getWater() end
            if reactor.getWaterCapacity then dados.water_capacity = reactor.getWaterCapacity() end
            if reactor.getSteam then dados.steam = reactor.getSteam() end
            if reactor.getSteamCapacity then dados.steam_capacity = reactor.getSteamCapacity() end
            if reactor.getProductionRate then dados.production_rate = reactor.getProductionRate() end
            if reactor.getEnergy then dados.energy = reactor.getEnergy() end
            if reactor.getMaxEnergy then dados.max_energy = reactor.getMaxEnergy() end
            
            print("📊 Reator: " .. (dados.plasma_temperature or 0) .. "°C")
            break
        end
    end
    
    return dados
end

local function coletarDadosTurbina()
    local dados = {}
    local perifericos = peripheral.getNames()
    
    for _, nome in ipairs(perifericos) do
        local tipo = peripheral.getType(nome)
        if tipo == "turbineValve" then
            local turbina = peripheral.wrap(nome)
            
            -- Coleta todos os dados disponíveis da turbina
            if turbina.getFlowRate then dados.flow_rate = turbina.getFlowRate() end
            if turbina.getMaxFlowRate then dados.max_flow_rate = turbina.getMaxFlowRate() end
            if turbina.getSteam then dados.steam = turbina.getSteam() end
            if turbina.getSteamCapacity then dados.steam_capacity = turbina.getSteamCapacity() end
            if turbina.getProductionRate then dados.production_rate = turbina.getProductionRate() end
            if turbina.getMaxProduction then dados.max_production = turbina.getMaxProduction() end
            if turbina.getEnergy then dados.energy = turbina.getEnergy() end
            if turbina.getMaxEnergy then dados.max_energy = turbina.getMaxEnergy() end
            
            print("📈 Turbina: " .. (dados.flow_rate or 0) .. "mb/t")
            break
        end
    end
    
    return dados
end

-- Funções de envio de dados
local function enviarDadosReator()
    dadosReator = coletarDadosReator()
    if next(dadosReator) ~= nil then
        if enviarMensagem("dados_reator", dadosReator) then
            -- Aguarda confirmação
            local resposta = receberMensagem(1)
            if resposta and resposta.tipo == "confirmacao" then
                print("✅ Dados do reator enviados")
                return true
            end
        end
    end
    return false
end

local function enviarDadosTurbina()
    dadosTurbina = coletarDadosTurbina()
    if next(dadosTurbina) ~= nil then
        if enviarMensagem("dados_turbina", dadosTurbina) then
            -- Aguarda confirmação
            local resposta = receberMensagem(1)
            if resposta and resposta.tipo == "confirmacao" then
                print("✅ Dados da turbina enviados")
                return true
            end
        end
    end
    return false
end

local function solicitarAnalise()
    if enviarMensagem("solicitar_analise") then
        local resposta = receberMensagem(2)
        if resposta and resposta.tipo == "analise" then
            analiseRecebida = resposta.dados
            print("📋 Análise recebida: " .. analiseRecebida.status_sistema)
            return true
        end
    end
    return false
end

-- Função para exibir dados na tela
local function exibirInterface()
    term.clear()
    term.setCursorPos(1, 1)
    
    print("=== FUSION REACTOR MONITOR ===")
    print("Servidor: " .. Config.SERVER_IP)
    print("Status: " .. (websocket and "CONECTADO" or "DESCONECTADO"))
    print("")
    
    -- Exibe dados do reator
    if next(dadosReator) ~= nil then
        print("🔵 REATOR:")
        print("  Plasma: " .. (dadosReator.plasma_temperature or 0) .. "°C")
        print("  Casco: " .. (dadosReator.case_temperature or 0) .. "°C")
        print("  Energia: " .. (dadosReator.energy or 0) .. "/" .. (dadosReator.max_energy or 0) .. " FE")
        if dadosReator.deuterium and type(dadosReator.deuterium) == "table" then
            print("  Deutério: " .. dadosReator.deuterium.amount .. "mb")
        end
    else
        print("🔵 REATOR: Nenhum dado")
    end
    
    print("")
    
    -- Exibe dados da turbina
    if next(dadosTurbina) ~= nil then
        print("🟢 TURBINA:")
        print("  Vazão: " .. (dadosTurbina.flow_rate or 0) .. "mb/t")
        print("  Produção: " .. (dadosTurbina.production_rate or 0) .. " FE/t")
        print("  Energia: " .. (dadosTurbina.energy or 0) .. "/" .. (dadosTurbina.max_energy or 0) .. " FE")
    else
        print("🟢 TURBINA: Nenhum dado")
    end
    
    print("")
    
    -- Exibe análise
    if next(analiseRecebida) ~= nil then
        print("📊 ANÁLISE:")
        print("  Status: " .. analiseRecebida.status_sistema)
        if analiseRecebida.alertas and #analiseRecebida.alertas > 0 then
            print("  ⚠️ Alertas: " .. #analiseRecebida.alertas)
            for i, alerta in ipairs(analiseRecebida.alertas) do
                if i <= 2 then  -- Mostra apenas os 2 primeiros
                    print("    - " .. alerta)
                end
            end
        else
            print("  ✅ Sem alertas")
        end
    else
        print("📊 ANÁLISE: Nenhuma análise")
    end
    
    print("")
    print("⏱️  Próxima atualização em " .. Config.UPDATE_INTERVAL .. "s")
    print("Pressione Ctrl+T para interromper")
end

-- Loop principal
local function mainLoop()
    local timer = os.startTimer(Config.UPDATE_INTERVAL)
    
    while true do
        local event, id, x, y = os.pullEvent()
        
        if event == "timer" and id == timer then
            -- Reconecta se necessário
            if not websocket then
                conectarServidor()
            end
            
            -- Envia dados e solicita análise
            if websocket then
                enviarDadosReator()
                enviarDadosTurbina()
                solicitarAnalise()
                exibirInterface()
            else
                print("❌ Sem conexão com o servidor")
            end
            
            timer = os.startTimer(Config.UPDATE_INTERVAL)
            
        elseif event == "websocket_closed" or event == "websocket_failure" then
            print("🔌 Conexão WebSocket perdida")
            websocket = nil
            
        elseif event == "terminate" then
            if websocket then
                websocket.close()
            end
            print("👋 Programa finalizado")
            break
        end
    end
end

-- Função principal
local function main()
    print("=== CLIENTE FUSION REACTOR ===")
    print("Conectando ao servidor Python...")
    
    if conectarServidor() then
        print("✅ Conectado! Iniciando monitoramento...")
        exibirInterface()
        mainLoop()
    else
        print("❌ Não foi possível conectar ao servidor")
        print("Verifique:")
        print("1. IP do servidor está correto?")
        print("2. Servidor Python está rodando?")
        print("3. Firewall permite a porta " .. Config.SERVER_PORT .. "?")
    end
end

-- Executa o programa
main()
