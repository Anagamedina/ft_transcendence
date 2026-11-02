<!--
  CLIENT USERS PANEL
  "Usuarios con acceso" block of the admin client detail (F23), as in the client
  design: the users of one organization, one ClientUserRow each (edit name and
  role, remove access). Data: users store (B6, GET /api/users?organization_id=).
  Loads the list when it is mounted, which is every time the "Usuarios" tab opens.
  Usage:
    <ClientUsersPanel :organization-id="client.id" @removed="..." />
-->

<template>
  <section
    class="rounded-xl border border-slate-200 bg-white p-5"
    aria-labelledby="client-users-title"
  >
    <header class="mb-2">
      <h2 id="client-users-title" class="font-bold text-slate-900">
        Usuarios con acceso
        <span v-if="loaded" class="font-normal text-slate-600"
          >({{ users.length }})</span
        >
      </h2>
      <p class="text-sm text-slate-600">Personas que ya tienen una cuenta.</p>
    </header>

    <LoadingState
      v-if="loading && users.length === 0"
      message="Cargando usuarios…"
    />

    <ErrorState v-else-if="loadError" :message="loadError" @retry="load" />

    <EmptyState
      v-else-if="users.length === 0"
      title="Este cliente aún no tiene usuarios"
      message="Invita a alguien de su equipo desde Invitaciones."
      icon="users"
      compact
    />

    <ul v-else>
      <ClientUserRow
        v-for="user in users"
        :key="user.id"
        :user="user"
        :is-self="user.id === sessionUserId"
        :remove="removeUser"
        @updated="onUpdated"
      />
    </ul>

    <!-- Result of the last action; role="status" announces it to screen readers -->
    <p
      v-if="feedback"
      role="status"
      class="mt-2 text-sm font-semibold text-success-dark"
    >
      {{ feedback }}
    </p>
  </section>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import ClientUserRow from "./ClientUserRow.vue";
import EmptyState from "./EmptyState.vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import { useUsersStore } from "../stores/users";
import { useAuthStore } from "../stores/auth";
import { apiErrorMessage } from "../utils/apiError";

const props = defineProps({
  // Organization whose users are listed
  organizationId: { type: String, required: true },
});

// removed(user): the parent reloads the client, so its user_count goes down
const emit = defineEmits(["removed"]);

const usersStore = useUsersStore();
const authStore = useAuthStore();

// The store is shared with other views: keep only this organization's users
const users = computed(() =>
  usersStore.items.filter(
    (user) => user.organization_id === props.organizationId,
  ),
);
const sessionUserId = computed(() => authStore.user?.id ?? null);

const loading = ref(false);
const loaded = ref(false);
const loadError = ref("");
const feedback = ref("");

async function load() {
  loading.value = true;
  loadError.value = "";
  try {
    // 100 is the API maximum per page; a client has a handful of users
    await usersStore.fetchUsers({
      organization_id: props.organizationId,
      page_size: 100,
    });
    loaded.value = true;
  } catch (err) {
    loadError.value = apiErrorMessage(
      err,
      "No se han podido cargar los usuarios.",
    );
  } finally {
    loading.value = false;
  }
}

function onUpdated(user) {
  feedback.value = `Se han guardado los cambios de ${user.name}.`;
}

// Called by the row. Lives here because the row unmounts as soon as the user
// leaves the store; the API error goes back to the row, which shows it
async function removeUser(user) {
  feedback.value = "";
  await usersStore.deleteUser(user.id);
  feedback.value = `${user.name} ya no tiene acceso a AquaGuard.`;
  emit("removed", user);
}

// On open, and again if the page moves to another client
watch(
  () => props.organizationId,
  () => {
    feedback.value = "";
    loaded.value = false;
    load();
  },
  { immediate: true },
);
</script>
