package com.saarathi.app.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.saarathi.app.data.RouteEntry
import com.saarathi.app.ui.theme.*

@Composable
fun SaarathiApp(vm: MainViewModel = viewModel()) {
    val state by vm.state.collectAsState()

    SaarathiTheme {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = Bg
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp, vertical = 24.dp)
            ) {
                // Header
                Text(
                    text = "Saarathi",
                    color = Teal,
                    fontSize = 30.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Your route should fit your journey.",
                    color = TextMuted,
                    fontSize = 14.sp,
                    modifier = Modifier.padding(top = 4.dp, bottom = 20.dp)
                )

                // Vehicle Selector Section
                Text(
                    text = "Vehicle",
                    color = TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 10.dp)
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val vehicles = listOf(
                        "bike" to "🏍️ Bike",
                        "car" to "🚗 Car",
                        "ev" to "⚡ EV"
                    )

                    vehicles.forEach { (type, label) ->
                        val selected = state.vehicle == type
                        FilterChip(
                            selected = selected,
                            onClick = { vm.setVehicle(type) },
                            label = {
                                Text(
                                    text = label,
                                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                    fontSize = 14.sp
                                )
                            },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Teal,
                                selectedLabelColor = Bg,
                                containerColor = CardBg,
                                labelColor = TextPrimary
                            ),
                            border = FilterChipDefaults.filterChipBorder(
                                enabled = true,
                                selected = selected,
                                borderColor = if (selected) Teal else CardBorder
                            ),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier.weight(1f)
                        )
                    }
                }

                // Battery Slider (for EV mode)
                if (state.vehicle == "ev") {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Battery: ${state.battery.toInt()}%",
                        color = TextPrimary,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Slider(
                        value = state.battery,
                        onValueChange = { vm.setBattery(it) },
                        valueRange = 0f..100f,
                        colors = SliderDefaults.colors(
                            thumbColor = Teal,
                            activeTrackColor = Teal,
                            inactiveTrackColor = CardBg
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Action Button
                Button(
                    onClick = { vm.compare() },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Teal,
                        contentColor = Bg
                    ),
                    enabled = !state.loading
                ) {
                    Text(
                        text = if (state.loading) "Evaluating Routes..." else "Compare routes",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                // Loading Indicator
                if (state.loading) {
                    Spacer(modifier = Modifier.height(24.dp))
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(color = Teal)
                    }
                }

                // Error Message
                if (state.error != null) {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Error: ${state.error}",
                        color = Risk,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                // Results
                state.result?.let { res ->
                    Spacer(modifier = Modifier.height(28.dp))

                    // Recommendation Card
                    Text(
                        text = "Recommendation",
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(bottom = 10.dp)
                    )

                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = CardBg),
                        border = BorderStroke(1.dp, Teal.copy(alpha = 0.6f))
                    ) {
                        Column(modifier = Modifier.padding(18.dp)) {
                            Text(
                                text = "Take Route ${res.bestIndex + 1}",
                                color = Teal,
                                fontSize = 26.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = res.explanation,
                                color = TextMuted,
                                fontSize = 14.sp,
                                lineHeight = 20.sp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    // All Candidate Routes
                    Text(
                        text = "All routes",
                        color = TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(bottom = 10.dp)
                    )

                    res.routes.forEach { route ->
                        RouteCard(
                            r = route,
                            isBest = (route.index == res.bestIndex)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                    }
                }
            }
        }
    }
}

@Composable
fun RouteCard(r: RouteEntry, isBest: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = CardBg),
        border = if (isBest) BorderStroke(1.5.dp, Teal) else BorderStroke(1.dp, CardBorder)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Route ${r.index + 1}${if (isBest) "  ★ Recommended" else ""}",
                    color = if (isBest) Teal else TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = "${r.score}/100",
                    color = if (isBest) Teal else TextPrimary,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Metrics row: Duration, Distance, Elevation
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "${r.etaMin} min",
                    color = TextMuted,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium
                )
                Text(text = "·", color = TextMuted, fontSize = 14.sp)
                Text(
                    text = "${r.distanceKm} km",
                    color = TextMuted,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium
                )
                Text(text = "·", color = TextMuted, fontSize = 14.sp)
                Text(
                    text = "↑ ${r.elevationGainM} m",
                    color = TextMuted,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            // EV Feasibility Badge
            r.ev?.let { ev ->
                Spacer(modifier = Modifier.height(10.dp))
                val (badgeText, badgeColor) = when (ev.status) {
                    "HIGH_RISK" -> "🔴 HIGH RISK" to Risk
                    "LOW_MARGIN" -> "🟡 LOW MARGIN" to Warn
                    else -> "🟢 FEASIBLE" to Green
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text(
                        text = badgeText,
                        color = badgeColor,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "— arrives at ${ev.arrivalPct}% (± ${ev.uncertaintyPct}%)",
                        color = TextMuted,
                        fontSize = 12.sp
                    )
                }
            }

            // Sub-scores summary
            Spacer(modifier = Modifier.height(10.dp))
            val subScoresFormatted = r.subScores.entries.joinToString(" · ") { (k, v) ->
                "${k.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }}: $v"
            }

            Text(
                text = subScoresFormatted,
                color = TextMuted.copy(alpha = 0.7f),
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
        }
    }
}
