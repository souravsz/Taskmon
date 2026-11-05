import { registerRootComponent } from 'expo';
import { AppRegistry } from 'react-native';

import { Main } from './src/main';
import { BANK_SMS_TASK, handleBankSms } from './src/utils/bankSms';

// Bank debit SMS → backend, also while the app is closed (started by the native receiver in modules/bank-sms).
AppRegistry.registerHeadlessTask(BANK_SMS_TASK, () => handleBankSms);

// registerRootComponent calls AppRegistry.registerComponent('main', () => Main).
registerRootComponent(Main);
