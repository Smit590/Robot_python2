
| *** Settings *** |
| Documentation  | This is the v1 test of G5/G5.5 FW release using telent protocol. |
| Library        | Infrastructure_Check.py |
| Library        | PPID_TEST.py |
| Library        | BC_reset.py |
| Library        | IdLed_test.py |
| Library        | Rack_num_change.py |

| *** Variables *** |
| ${EMPTY}         | "" |
| ${MC_IP}         | 192.168.0.194 |
| ${USER_NAME}     | ${EMPTY} |
| ${PASSWORD}      | ${EMPTY} |
| ${INFRA}         | ${EMPTY} |
| ${output}        | ${EMPTY} |
| ${Loop}		   | 1 |

| ${DOWNGRADE_RET} | ${EMPTY} |
| ${UPGRADE_RET}   | ${EMPTY} |
| ${UPGRADE_DOWNGRADE_RET}   | ${EMPTY} |

| ${UPGRADE}       | upgrade  |
| ${DOWNGRADE}     | downgrade |
| ${UPGRADE_DOWNGRADE}     | upgrade_downgrade |
| ${RERUN_LOG}         | ${EMPTY} |
    
| *** Test Cases *** |

| Infrastructure_Test |
|	 | [Tags] | Infrastructure_Test |
|    | ${INFRA}=     | Infrastructure | ${MC_IP} | ${Loop} | ${USER_NAME} | ${PASSWORD} |
|    | Run Keyword If | '${INFRA}' != 'G5'  and  '${INFRA}' != 'G5.5'  | FAIL |
|    | Log | ${INFRA} |
|    | Set Global Variable | ${INFRA} |

| PPID_TEST |
|	 | [Tags] | PPID_TEST |
|    | ${output}=      | PPID SET Test | ${MC_IP} | ${Loop} | ${USER_NAME} | ${PASSWORD} |
|    | Run Keyword If  | '${output}' == 'FAIL' | FAIL |

| BC_Reset_Test |
|	 | [Tags] | BC_Reset_Test |
|    | ${output}=      | BC Reset Test | ${MC_IP} | ${Loop} | ${USER_NAME} | ${PASSWORD} |
|    | Run Keyword If  | '${output}' == 'FAIL' | FAIL |

| IdLed_ON/OFF_Test   |
|	 | [Tags] | IdLed_ON/OFF_Test |
|    | ${output}=     | IdLed | ${MC_IP} | ${Loop} | ${USER_NAME} | ${PASSWORD} |
|    | Run Keyword If | '${output}' == 'FAIL' | FAIL |

| Rack_num_change_test |
|	 | [Tags] | Rack_num_change_test |
|    | ${output}=      | Rack num change test | ${MC_IP} | ${Loop} | ${USER_NAME} | ${PASSWORD} |
|    | Run Keyword If  | '${output}' == 'FAIL' | FAIL |

| *** Keywords *** |

| Infrastructure |
|    | [Arguments] | ${arg_0} | ${arg_1} | ${arg_2} | ${arg_3} |
|    | ${iRet} =   | check_Infrastructure | ${arg_0} | ${arg_1} | ${arg_2} | ${arg_3} |
|    | [Return]    | ${iRet} |

| PPID SET Test |
|    | [Arguments] | ${arg_0} | ${arg1} | ${arg_2} | ${arg_3} |
|    | ${iRet} =   | SET_PPID_TEST  | ${arg_0} | ${arg1} | ${arg_2} | ${arg_3} |
|    | [Return]    | ${iRet} |

| BC Reset Test |
|    | [Arguments] | ${arg_0} | ${arg1} | ${arg_2} | ${arg_3} |
|    | ${iRet} =   | BC_Reset  | ${arg_0} | ${arg1} | ${arg_2} | ${arg_3} |
|    | [Return]    | ${iRet} |

| IdLed |
|    | [Arguments] | ${arg_0} | ${arg_1} | ${arg_2} | ${arg_3} |
|    | ${iRet} =   | IdLedState_ON_OFF | ${arg_0} | ${arg_1} | ${arg_2} | ${arg_3} |
|    | [Return]    | ${iRet} |

| Rack num change test |
|    | [Arguments] | ${arg_0} | ${arg1} | ${arg_2} | ${arg_3} |
|    | ${iRet} =   | Rack_num_change | ${arg_0} | ${arg1} | ${arg_2} | ${arg_3} |
|    | [Return]    | ${iRet} |


