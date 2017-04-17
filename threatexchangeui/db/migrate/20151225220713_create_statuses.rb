class CreateStatuses < ActiveRecord::Migration
  def change
    create_table :statuses do |t|
      t.string :name
      t.text :description

      t.timestamps null: false
    end
    add_index :statuses, :name
  end
end
