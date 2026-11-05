package expo.modules.banksms

import android.content.Context
import android.provider.Telephony
import expo.modules.kotlin.exception.Exceptions
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

/**
 * readBankDebits(sinceMillis): the Federal Bank debit SMS in the inbox received after that time, oldest
 * first, as { text, date }. The app sends them to the backend when it opens, which catches payments missed
 * while offline or while the phone kept the app from running. Needs READ_SMS.
 */
class BankSmsModule : Module() {
  private val context: Context
    get() = appContext.reactContext ?: throw Exceptions.ReactContextLost()

  override fun definition() = ModuleDefinition {
    Name("BankSms")

    AsyncFunction("readBankDebits") { sinceMillis: Double ->
      val found = mutableListOf<Map<String, Any>>()
      val cursor = context.contentResolver.query(
        Telephony.Sms.Inbox.CONTENT_URI,
        arrayOf(Telephony.Sms.BODY, Telephony.Sms.DATE),
        "${Telephony.Sms.DATE} > ? AND ${Telephony.Sms.BODY} LIKE ?",
        arrayOf(sinceMillis.toLong().toString(), "%Federal Bank%"),
        "${Telephony.Sms.DATE} ASC",
      )
      cursor?.use {
        while (it.moveToNext()) {
          val text = it.getString(0) ?: continue
          if (BankSmsReceiver.isBankDebit(text)) {
            found.add(mapOf("text" to text, "date" to it.getLong(1).toDouble()))
          }
        }
      }
      found
    }
  }
}
