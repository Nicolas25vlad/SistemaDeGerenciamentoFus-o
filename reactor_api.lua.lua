-- Fusion Reactor Raw Data Collector
-- Apenas coleta dados brutos, zero processamento

local Settings = {
    UpdateInterval = 1,
    APIPort = 8080
}

local rawData = {}

function CollectRawData()
    local peripherals = peripheral.getNames()
    local data = {
        timestamp = os.epoch("utc"),
        reactor = {},
        turbine = {},
        peripherals_found = {}
    }
    
    for _, name in ipairs(peripherals) do
        local p = peripheral.wrap(name)
        local pType = peripheral.getType(name)
        
        data.peripherals_found[name] = pType
        
        if pType == "fusionReactorLogicAdapter" then
            data.reactor = GetReactorRawData(p)
        elseif pType == "turbineValve" then
            data.turbine = GetTurbineRawData(p)
        end
    end
    
    rawData = data
    return data
end

function GetReactorRawData(reactor)
    local data = {}
    
    -- Apenas chama as funções e guarda os valores brutos
    if reactor.getDeuterium then data.deuterium = reactor.getDeuterium() end
    if reactor.getDeuteriumCapacity then data.deuterium_capacity = reactor.getDeuteriumCapacity() end
    
    if reactor.getTritium then data.tritium = reactor.getTritium() end
    if reactor.getTritiumCapacity then data.tritium_capacity = reactor.getTritiumCapacity() end
    
    if reactor.getDTFuel then data.dt_fuel = reactor.getDTFuel() end
    if reactor.getInjectionRate then data.injection_rate = reactor.getInjectionRate() end
    
    if reactor.getPlasmaTemperature then data.plasma_temperature = reactor.getPlasmaTemperature() end
    if reactor.getMaxPlasmaTemperature then data.max_plasma_temperature = reactor.getMaxPlasmaTemperature(false) end
    
    if reactor.getCaseTemperature then data.case_temperature = reactor.getCaseTemperature() end
    if reactor.getMaxCasingTemperature then data.max_case_temperature = reactor.getMaxCasingTemperature(false) end
    
    if reactor.getWater then data.water = reactor.getWater() end
    if reactor.getWaterCapacity then data.water_capacity = reactor.getWaterCapacity() end
    
    if reactor.getSteam then data.steam = reactor.getSteam() end
    if reactor.getSteamCapacity then data.steam_capacity = reactor.getSteamCapacity() end
    
    if reactor.getProductionRate then data.production_rate = reactor.getProductionRate() end
    
    if reactor.getEnergy then data.energy = reactor.getEnergy() end
    if reactor.getMaxEnergy then data.max_energy = reactor.getMaxEnergy() end
    
    return data
end

function GetTurbineRawData(turbine)
    local data = {}
    
    if turbine.getFlowRate then data.flow_rate = turbine.getFlowRate() end
    if turbine.getMaxFlowRate then data.max_flow_rate = turbine.getMaxFlowRate() end
    
    if turbine.getSteam then data.steam = turbine.getSteam() end
    if turbine.getSteamCapacity then data.steam_capacity = turbine.getSteamCapacity() end
    
    if turbine.getProductionRate then data.production_rate = turbine.getProductionRate() end
    if turbine.getMaxProduction then data.max_production = turbine.getMaxProduction() end
    
    if turbine.getEnergy then data.energy = turbine.getEnergy() end
    if turbine.getMaxEnergy then data.max_energy = turbine.getMaxEnergy() end
    
    return data
end

-- Servidor HTTP mínimo
function StartHTTPServer()
    http.websocket(Settings.APIPort)
    print("Raw Data API rodando na porta " .. Settings.APIPort)
end

function HandleHTTPRequests()
    while true do
        local event, url, method = os.pullEvent("http_request")
        
        local response = {
            code = 200,
            headers = { ["Content-Type"] = "application/json" },
            data = "{}"
        }
        
        if url == "/api/raw" and method == "GET" then
            response.data = SerializeToJSON(rawData)
        elseif url == "/api/health" and method == "GET" then
            response.data = '{"status":"online"}'
        else
            response.code = 404
        end
        
        http.respond(response)
    end
end

function SerializeToJSON(data)
    local json = {}
    
    local function serializeValue(value)
        if type(value) == "string" then
            return '"' .. value .. '"'
        elseif type(value) == "number" then
            return tostring(value)
        elseif type(value) == "boolean" then
            return value and "true" or "false"
        elseif type(value) == "table" then
            if value.amount and value.name then -- Fluid data
                return string.format('{"amount":%d,"name":"%s"}', value.amount, value.name)
            else
                return "{}"
            end
        else
            return 'null'
        end
    end
    
    for k, v in pairs(data) do
        table.insert(json, '"' .. k .. '":' .. serializeValue(v))
    end
    return "{" .. table.concat(json, ",") .. "}"
end

function MainLoop()
    local timerUpdate = os.startTimer(Settings.UpdateInterval)
    
    while true do
        local event, param1 = os.pullEvent()
        
        if event == "timer" and param1 == timerUpdate then
            CollectRawData()
            timerUpdate = os.startTimer(Settings.UpdateInterval)
        end
    end
end

function Main()
    print("=== FUSION REACTOR RAW DATA COLLECTOR ===")
    print("Coletando dados brutos...")
    
    -- Coleta inicial
    CollectRawData()
    
    StartHTTPServer()
    parallel.waitForAll(MainLoop, HandleHTTPRequests)
end

Main()