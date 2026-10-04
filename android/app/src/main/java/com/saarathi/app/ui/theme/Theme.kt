package com.saarathi.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColors = darkColorScheme(
    primary = Teal,
    background = Bg,
    surface = CardBg,
    onPrimary = Bg,
    onBackground = TextPrimary,
    onSurface = TextPrimary
)

@Composable
fun SaarathiTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColors,
        content = content
    )
}
