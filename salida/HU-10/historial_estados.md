# Historial de estados · hilo HU-10-solicitar-vacaciones-20261105-1113

| # | Paso | Nodo que corrió | Siguiente nodo | Ciclos | Intentos | Hora | Checkpoint |
|---|---|---|---|---|---|---|---|
| 1 | -1 | (entrada) | __start__ | 0 | 0 | 11:13:29 | `1f1d93c3-8a67` |
| 2 | 0 | __start__ | filtrar_historia | 0 | 0 | 11:13:29 | `1f1d93c3-8a6a` |
| 3 | 1 | filtrar_historia | analizar | 0 | 0 | 11:13:32 | `1f1d93c3-a9aa` |
| 4 | 2 | analizar | pedir_aclaracion | 0 | 0 | 11:15:36 | `1f1d93c8-486e` |
| 5 | 3 | pedir_aclaracion | disenar_casos | 0 | 0 | 11:25:29 | `1f1d93de-56bb` |
| 6 | 4 | disenar_casos | planificar | 0 | 0 | 11:32:34 | `1f1d93ee-3234` |
| 7 | 5 | planificar | aprobar_plan | 0 | 0 | 11:32:57 | `1f1d93ef-0ff1` |
| 8 | 6 | aprobar_plan | planificar | 0 | 0 | 11:35:07 | `1f1d93f3-e201` |
| 9 | 7 | planificar | aprobar_plan | 0 | 0 | 11:35:31 | `1f1d93f4-c83e` |
| 10 | 8 | aprobar_plan | construir | 0 | 0 | 11:36:47 | `1f1d93f7-9bb1` |
| 11 | 9 | construir | verificar | 0 | 1 | 11:40:32 | `1f1d93ff-ffd5` |
| 12 | 10 | verificar | desplegar, automatizar | 0 | 1 | 11:40:34 | `1f1d9400-0f40` |
| 13 | 11 | desplegar, automatizar | listo | 0 | 1 | 11:42:52 | `1f1d9405-3703` |
| 14 | 12 | listo | pruebas_e2e | 0 | 1 | 11:42:52 | `1f1d9405-3706` |
| 15 | 13 | pruebas_e2e | fin | 0 | 1 | 11:43:02 | `1f1d9405-9266` |

El checkpoint del propio nodo `fin` se guarda después de escribir este archivo, por eso no aparece.
