class CreateShareLevelTypes < ActiveRecord::Migration
  def change
    create_table :share_level_types do |t|
      t.string :name
      t.text :description

      t.timestamps null: false
    end
    add_index :share_level_types, :name
  end
end
