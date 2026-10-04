package com.saarathi.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.saarathi.app.data.CompareResponse
import com.saarathi.app.data.Repository
import com.saarathi.app.data.RouteRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class UiState(
    val loading: Boolean = false,
    val vehicle: String = "bike",
    val battery: Float = 100f,
    val result: CompareResponse? = null,
    val error: String? = null
)

class MainViewModel : ViewModel() {

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    fun setVehicle(v: String) {
        _state.update { it.copy(vehicle = v) }
    }

    fun setBattery(b: Float) {
        _state.update { it.copy(battery = b) }
    }

    fun compare() {
        val currentVehicle = _state.value.vehicle
        val currentBattery = _state.value.battery

        _state.update { it.copy(loading = true, error = null) }

        viewModelScope.launch {
            try {
                // Demo coordinates Bengaluru: MG Road -> Koramangala
                val request = RouteRequest(
                    startLat = 12.9756,
                    startLon = 77.6068,
                    endLat = 12.9352,
                    endLon = 77.6244,
                    vehicle = currentVehicle,
                    batteryPct = currentBattery.toDouble()
                )

                val response = Repository.compare(request)
                _state.update { it.copy(loading = false, result = response, error = null) }
            } catch (e: Exception) {
                _state.update {
                    it.copy(
                        loading = false,
                        error = e.localizedMessage ?: "Failed to connect to Saarathi backend."
                    )
                }
            }
        }
    }
}
