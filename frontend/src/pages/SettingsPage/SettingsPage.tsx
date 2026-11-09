import { ProfileSection } from './ProfileSection'
import { PasswordSection } from './PasswordSection'
import { DeleteAccountSection } from './DeleteAccountSection'
import styles from './SettingsPage.module.css'

export function SettingsPage() {
  return (
    <>
      <h1 className={styles.title}>Configurações</h1>
      <p className={styles.lead}>Gerencie seus dados de acesso e sua conta.</p>
      <div className={styles.sections}>
        <ProfileSection />
        <PasswordSection />
        <DeleteAccountSection />
      </div>
    </>
  )
}
