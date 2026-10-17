<template>
  <!-- Shared panel (personal data and password) plus the client-only cards.
       The admin account view uses the same panel without these slots. -->
  <AccountPanel>
    <template #after-profile>
      <SubscriptionCard />
    </template>
    <template #after-password>
      <PrivacyCard />
    </template>
  </AccountPanel>
</template>

<script setup>
import AccountPanel from '../../components/AccountPanel.vue'
import SubscriptionCard from '../../components/account/SubscriptionCard.vue'
import PrivacyCard from '../../components/account/PrivacyCard.vue'
</script>
