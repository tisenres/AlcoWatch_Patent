package com.alcowatch.wearos.presentation

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.wear.compose.material.*
import dagger.hilt.android.AndroidEntryPoint
import timber.log.Timber

/**
 * Main Activity for AlcoWatch Wear OS Application
 * Displays real-time BAC monitoring and sensor status
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Timber.d("MainActivity created")

        setContent {
            AlcoWatchApp()
        }
    }

    override fun onResume() {
        super.onResume()
        Timber.d("MainActivity resumed")
    }

    override fun onPause() {
        super.onPause()
        Timber.d("MainActivity paused")
    }
}

/**
 * Main Compose UI for AlcoWatch
 */
@Composable
fun AlcoWatchApp() {
    MaterialTheme {
        Scaffold(
            timeText = {
                TimeText()
            }
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black)
                    .padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "AlcoWatch",
                    style = MaterialTheme.typography.title2,
                    color = Color.White,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "Alcohol Detection System",
                    style = MaterialTheme.typography.body2,
                    color = Color.Gray,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(24.dp))

                // BAC Display
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    onClick = { /* TODO: Show details */ }
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "BAC Level",
                            style = MaterialTheme.typography.caption1,
                            color = Color.Gray
                        )
                        Text(
                            text = "0.000",
                            style = MaterialTheme.typography.display1,
                            color = Color(0xFF4CAF50)
                        )
                        Text(
                            text = "g/dL",
                            style = MaterialTheme.typography.caption1,
                            color = Color.Gray
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "Status: Ready",
                    style = MaterialTheme.typography.body2,
                    color = Color(0xFF4CAF50),
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}
