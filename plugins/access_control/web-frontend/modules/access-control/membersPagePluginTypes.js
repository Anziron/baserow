import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import MemberPermissionField from '@access-control/components/MemberPermissionField'

/**
 * Access Control Members Page Plugin Type
 * 
 * Adds a "Permissions" column to the members table that allows
 * workspace admins to manage plugin and structure permissions for each member.
 */
export class AccessControlMembersPagePluginType extends MembersPagePluginType {
  static getType() {
    return 'access_control_members'
  }

  /**
   * Add a permissions column to the members table
   */
  mutateMembersTableColumns(columns, context) {
    // Find the index of the "more" column (last column)
    const moreColumnIndex = columns.findIndex((column) => column.key === null)
    
    // Create the permissions column
    const permissionsColumn = new CrudTableColumn(
      'access_control_permissions',
      this.app.i18n.t('accessControl.workspace.permissions'),
      MemberPermissionField,
      false,  // sortable
      false,  // searchable
      false,  // isMore
      { workspaceId: context.workspace.id },
      15  // width
    )

    // Insert before the "more" column
    if (moreColumnIndex !== -1) {
      columns.splice(moreColumnIndex, 0, permissionsColumn)
    } else {
      columns.push(permissionsColumn)
    }

    return columns
  }

  /**
   * Check if this plugin should be deactivated
   * Only workspace admins can see the permissions column
   */
  isDeactivated(workspaceId) {
    // Check if user has admin permission for this workspace
    const workspace = this.app.store.getters['workspace/get'](workspaceId)
    if (!workspace) {
      return true
    }
    
    // Only show for workspace admins
    return workspace.permissions !== 'ADMIN'
  }

  /**
   * Get the modal component for managing member permissions
   */
  getModalComponent() {
    return () => import('@access-control/components/MemberPermissionModal')
  }
}
