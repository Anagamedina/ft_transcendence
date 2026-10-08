<!--
  ADMIN SITES VIEW
  Lists all sites. Clicking a site opens its client detail. Rendered inside AdminLayout.
  Uses temporary fixture data until the sites store exists (data area).
-->

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import SitesSummary from '../../components/SitesSummary.vue'
// TODO: replace with sites store data (data area) and delete this import
import { sites as mockSites } from '../../services/fixtures/sites'

const router = useRouter()

// Kept for the future filters; not used to filter yet
const search = ref('')

function openSiteClient(site) {
  router.push(`/admin/clients/${site.organization_id}`)
}
</script>

<template>
  <AdminLayout>
    <div class="p-6 space-y-4">
      <!-- Search box: visual only. Filtering logic belongs to the data/state area -->
      <label class="block w-full sm:w-72 sm:ml-auto">
        <span class="sr-only">Buscar site</span>
        <input
          v-model="search"
          type="search"
          placeholder="Buscar site…"
          class="input input-bordered w-full"
        />
      </label>

      <SitesSummary :sites="mockSites" selectable @select="openSiteClient" />
    </div>
  </AdminLayout>
</template>